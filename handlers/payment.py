"""Подтверждение оплаты: автоматическое через ЮKassa (если заказ создавался
с точной числовой суммой) либо ручная схема по СБП для остальных заказов.

Статусы заказа:
- Автоматическая оплата (есть yookassa_payment_id): «ожидает оплаты» →
  клиент нажал «Я оплатил(а)» → бот САМ проверяет статус в ЮKassa →
  «оплачен» (только если ЮKassa подтвердила succeeded), иначе статус не
  меняется и клиенту честно говорят, что оплата ещё не прошла.
- Ручная схема (нет yookassa_payment_id): «ожидает оплаты» → клиент нажал
  «Я оплатил(а)» → «на проверке» → владелец нажал «Подтвердить оплату» →
  «оплачен». Кнопка «Подтвердить оплату» приходит владельцу в его личном
  чате с ботом — её видит и может нажать только он.

Граничные случаи:
- Повторное «Я оплатил(а)» по заказу, который уже на проверке/оплачен —
  не пересоздаёт заявку на проверку, просто напоминает подождать.
- Повторное «Подтвердить оплату» по уже оплаченному заказу — игнорируется
  с уведомлением "уже подтверждено", статус не трогаем повторно.
- «Подтвердить оплату» на заказе, который клиент ещё не отмечал оплаченным
  (статус «ожидает оплаты») — тоже отклоняется: подтвердить можно только
  то, что клиент уже сам пометил как оплаченное (services.cart.can_confirm_payment).
- ЮKassa вернула что угодно кроме "succeeded" (pending/canceled/ошибка
  запроса) — статус заказа НЕ меняется, повторное нажатие безопасно.
- Если ADMIN_CHAT_ID не задан, клиент всё равно получает честный ответ
  (см. также services/notify.py — там уже есть safe-фолбэк с логированием).
"""
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from config import ADMIN_CHAT_ID
from keyboards.inline import admin_advance_stage_kb, admin_confirm_payment_kb
from services import yookassa
from services.cart import STAGE_TITLES, can_confirm_payment, get_order, set_initial_stage, set_order_status
from services.notify import notify_admin

router = Router()

STATUS_AWAITING = "ожидает оплаты"
STATUS_REVIEW = "на проверке"
STATUS_PAID = "оплачен"


async def _mark_paid_and_notify(callback: CallbackQuery, order_id: int, order: dict) -> None:
    """Общий финальный шаг и для автоматического, и для ручного пути:
    ставим статус «оплачен», первый этап работы и уведомляем клиента."""
    await set_order_status(order_id, STATUS_PAID)
    await set_initial_stage(order_id)

    await callback.bot.send_message(
        order["telegram_user_id"],
        f"🎉 Оплата заказа №{order_id} подтверждена! Начинаем работу — "
        f"сейчас на этапе «{STAGE_TITLES[0]}». Прогресс можно посмотреть "
        "в «🗺 Этапы работы» в меню.",
    )


@router.callback_query(F.data.startswith("order:paid:"))
async def client_marked_paid(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[-1])
    order = await get_order(order_id)

    await callback.answer()

    if order is None:
        await callback.message.answer("Не нашёл этот заказ — возможно, что-то пошло не так.")
        return

    if order["status"] != STATUS_AWAITING:
        # Граничный случай: повторное нажатие «Я оплатил(а)».
        await callback.message.answer(
            f"Заказ №{order_id} уже на проверке или оплачен — просто подожди подтверждения 🙂"
        )
        return

    payment_id = order.get("yookassa_payment_id")

    if payment_id:
        # Автоматическая проверка через ЮKassa — статус меняется ТОЛЬКО если
        # провайдер реально подтвердил оплату, а не потому что клиент нажал кнопку.
        status = await yookassa.get_payment_status(payment_id)

        if yookassa.is_payment_confirmed(status):
            await _mark_paid_and_notify(callback, order_id, order)
            return

        await callback.message.answer(
            "Пока не вижу подтверждённой оплаты от ЮKassa 🤔\n"
            "Заверши оплату по ссылке выше и нажми «Я оплатил(а)» ещё раз."
        )
        return

    # Ручная схема (СБП) — без прямой проверки у провайдера, подтверждает владелец.
    await set_order_status(order_id, STATUS_REVIEW)

    await callback.message.answer(
        f"Спасибо! Заказ №{order_id} отправлен на проверку оплаты — "
        "как только владелец подтвердит перевод, я сразу напишу."
    )

    user = callback.from_user
    who = f"@{user.username}" if user.username else user.full_name

    await notify_admin(
        callback.bot,
        ADMIN_CHAT_ID,
        f"💳 Клиент отметил заказ №{order_id} как оплаченный, ожидает подтверждения.\n\n"
        f"Сумма: {order['total_text']}\n"
        f"От: {who} (id {user.id})\n\n"
        "Проверь перевод и подтверди 👇",
        reply_markup=admin_confirm_payment_kb(order_id),
    )


@router.callback_query(F.data.startswith("order:confirm:"))
async def admin_confirm_payment(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[-1])
    order = await get_order(order_id)

    if order is None:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    if not can_confirm_payment(order):
        # Граничный случай: заказ уже оплачен (повторное нажатие) ИЛИ клиент
        # ещё не отмечал оплату — подтверждать нечего в обоих случаях.
        msg = "Уже подтверждено ранее" if order["status"] == STATUS_PAID else "Клиент ещё не отметил оплату"
        await callback.answer(msg, show_alert=True)
        return

    await callback.answer("Оплата подтверждена ✅")
    await _mark_paid_and_notify(callback, order_id, order)

    try:
        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ Оплата подтверждена. Этап: «{STAGE_TITLES[0]}».",
            reply_markup=admin_advance_stage_kb(order_id, STAGE_TITLES[0]),
        )
    except TelegramBadRequest:
        pass
