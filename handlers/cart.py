"""«Корзина»: показ содержимого, удаление позиций, оформление заказа.

Добавление позиций происходит в handlers/showcase.py (кнопка «Добавить в
корзину» под карточкой витрины) — здесь только просмотр, изменение и
оформление того, что туда уже попало. Подтверждение оплаты (кнопки
«Я оплатил(а)» / «Подтвердить оплату») — в handlers/payment.py.

Граничные случаи, которые обрабатываются явно:
- Пустая корзина при открытии — вежливое сообщение + подсказка про витрину.
- «Убрать» дважды по одной позиции — второй раз тихо игнорируется
  (remove_item вернёт False), краша нет, сообщение просто перерисовывается.
- «Оформить заказ» с пустой корзиной (например, успели убрать всё в
  соседней вкладке или дважды нажать «Оформить») — заказ не создаётся,
  показывается предупреждение и пустой вид корзины.
- Повторное редактирование сообщения тем же содержимым (Telegram ругается
  "message is not modified") — перехватываем и просто игнорируем.
"""
import re

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from keyboards.inline import cart_kb, online_payment_kb
from keyboards.reply import BTN_CART
from services import yookassa
from services.cart import (
    CartLine,
    can_checkout,
    create_order,
    format_total,
    get_cart,
    get_exact_total,
    remove_item,
    set_yookassa_payment_id,
)

router = Router()

EMPTY_CART_TEXT = (
    "Корзина пока пуста 🛒\n"
    "Загляни в «🛍 Витрина» в меню внизу, чтобы выбрать услуги."
)


def _render_cart_text(lines: list[CartLine]) -> str:
    rows = []
    for i, line in enumerate(lines, start=1):
        qty_suffix = f" × {line.quantity}" if line.quantity > 1 else ""
        rows.append(f"{i}. {line.title}{qty_suffix} — {line.price_text}")
    total = format_total(lines)
    return "🛒 Ваша корзина:\n\n" + "\n".join(rows) + f"\n\nИтого: {total}"


def build_checkout_message(order_id: int, lines: list[CartLine] | list[dict], payment: dict | None) -> tuple[str, object | None]:
    """Формирует текст чека и клавиатуру после оформления заказа.

    Для всех точных сумм путь только через ЮKassa. Для нечисловых заказов
    мы не показываем старую схему оплаты по СБП: ветка оплаты должна быть
    либо онлайн, либо отсутствовать совсем.
    """
    normalized: list[CartLine] = []
    for index, line in enumerate(lines, start=1):
        if hasattr(line, "title"):
            normalized.append(line)
            continue

        title = line["title"]
        price_text = line["price_text"]
        quantity = int(line.get("quantity", 1))
        digits = re.sub(r"[^\d]", "", price_text)
        line_price = int(digits) * quantity if digits else None
        is_approx = price_text.strip().lower().startswith("от")
        normalized.append(
            CartLine(
                slug=f"item_{index}",
                title=title,
                price_text=price_text,
                quantity=quantity,
                line_price=line_price,
                is_approx=is_approx,
            )
        )

    rows = []
    for i, line in enumerate(normalized, start=1):
        qty_suffix = f" × {line.quantity}" if line.quantity > 1 else ""
        rows.append(f"{i}. {line.title}{qty_suffix} — {line.price_text}")
    total = format_total(normalized)
    items_block = "\n".join(rows) + f"\n\nИтого: {total}\n\n"

    if payment is not None:
        text = (
            f"✅ Заказ №{order_id} оформлен, статус — «ожидает оплаты».\n\n"
            + items_block
            + "💳 Оплата через ЮKassa:\n"
            "Нажми «Оплатить онлайн», заверши оплату и вернись сюда — "
            "я проверю платёж автоматически."
        )
        keyboard = online_payment_kb(order_id, payment["confirmation_url"])
    else:
        text = (
            f"✅ Заказ №{order_id} оформлен, статус — «ожидает оплаты».\n\n"
            + items_block
            + "⚠️ Онлайн-оплата для этого заказа пока недоступна.\n"
            "Напиши владельцу в Telegram, чтобы согласовать детали оплаты."
        )
        keyboard = None

    return text, keyboard


@router.message(F.text == BTN_CART)
async def show_cart(message: Message) -> None:
    lines = await get_cart(message.from_user.id)
    if not lines:
        await message.answer(EMPTY_CART_TEXT)
        return
    await message.answer(_render_cart_text(lines), reply_markup=cart_kb(lines))


@router.callback_query(F.data.startswith("cart:remove:"))
async def remove_from_cart(callback: CallbackQuery) -> None:
    slug = callback.data.split(":", 2)[-1]
    user_id = callback.from_user.id

    removed = await remove_item(user_id, slug)
    await callback.answer("Убрано из корзины" if removed else "Этой позиции уже нет в корзине")

    lines = await get_cart(user_id)
    try:
        if not lines:
            await callback.message.edit_text(EMPTY_CART_TEXT)
        else:
            await callback.message.edit_text(_render_cart_text(lines), reply_markup=cart_kb(lines))
    except TelegramBadRequest:
        pass  # содержимое не изменилось (Telegram не даёт редактировать "в то же самое")


@router.callback_query(F.data == "cart:checkout")
async def checkout(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lines = await get_cart(user_id)

    if not can_checkout(lines):
        await callback.answer("Корзина уже пуста", show_alert=True)
        try:
            await callback.message.edit_text(EMPTY_CART_TEXT)
        except TelegramBadRequest:
            pass
        return

    await callback.answer()
    order_id = await create_order(user_id, lines)

    rows = []
    for i, line in enumerate(lines, start=1):
        qty_suffix = f" × {line.quantity}" if line.quantity > 1 else ""
        rows.append(f"{i}. {line.title}{qty_suffix} — {line.price_text}")
    total = format_total(lines)
    items_block = "\n".join(rows) + f"\n\nИтого: {total}\n\n"

    # Если сумма полностью числовая и ЮKassa настроена — создаём онлайн-платёж.
    # В ручной СБП-схеме нет необходимости: бот больше не предлагает её как
    # способ оплаты.
    exact_total = get_exact_total(lines)
    payment = None
    if exact_total is not None and yookassa.is_configured():
        payment = await yookassa.create_payment(
            amount_rub=exact_total,
            description=f"Заказ №{order_id} — VibeCoder",
            return_url="https://t.me/vibecoderassistant_bot",
        )

    if payment is not None:
        await set_yookassa_payment_id(order_id, payment["id"])

    text, keyboard = build_checkout_message(order_id, lines, payment)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard)
