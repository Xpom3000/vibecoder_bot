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
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from data.portfolio import PAYMENT
from keyboards.inline import cart_kb, order_payment_kb
from keyboards.reply import BTN_CART
from services.cart import CartLine, can_checkout, create_order, format_total, get_cart, remove_item

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

    text = (
        f"✅ Заказ №{order_id} оформлен, статус — «ожидает оплаты».\n\n"
        + "\n".join(rows)
        + f"\n\nИтого: {total}\n\n"
        f"💳 Оплата — {PAYMENT['method']}:\n"
        f"Телефон: {PAYMENT['phone']}\n"
        f"Банк: {PAYMENT['bank']}\n"
        f"Получатель: {PAYMENT['recipient']}\n\n"
        "Переведи сумму заказа и нажми кнопку ниже — я передам владельцу "
        "на проверку и он подтвердит оплату вручную."
    )

    try:
        await callback.message.edit_text(text, reply_markup=order_payment_kb(order_id))
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=order_payment_kb(order_id))
