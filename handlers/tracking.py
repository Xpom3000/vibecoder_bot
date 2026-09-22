"""Продвижение заказа по этапам работы: «Бриф → Прототип → Дизайн → Сборка →
Передача» (data/portfolio.py, STAGES).

Кнопка «➡️ Следующий этап» приходит владельцу в его личном чате с ботом —
вместе с подтверждением оплаты (handlers/payment.py) и после каждого
перехода. Владелец двигает заказ вручную по факту реального прогресса, а
не по таймеру или автоматике — трекинг честный, а не выдуманный.

При каждом переходе клиенту уходит уведомление с новым этапом.

Граничный случай: повторное/лишнее нажатие «Следующий этап», когда заказ
уже на последнем этапе — advance_order_stage() вернёт None, обработчик
вежливо сообщает об этом и ничего не ломает.
"""
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from data.portfolio import STAGES
from keyboards.inline import admin_advance_stage_kb
from services.cart import STAGE_TITLES, advance_order_stage, get_order

router = Router()

_STAGE_DESCRIPTIONS = {s["title"]: s["description"] for s in STAGES}


@router.callback_query(F.data.startswith("order:advance:"))
async def advance_stage(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[-1])
    new_stage = await advance_order_stage(order_id)

    if new_stage is None:
        await callback.answer("Дальше двигать некуда — заказ уже на последнем этапе", show_alert=True)
        return

    await callback.answer(f"Переведено на этап «{new_stage}»")

    order = await get_order(order_id)
    is_last = new_stage == STAGE_TITLES[-1]

    # Обновляем кнопку под сообщением владельца: на следующий этап,
    # либо убираем кнопку совсем, если этап последний.
    try:
        if is_last:
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            await callback.message.edit_reply_markup(reply_markup=admin_advance_stage_kb(order_id, new_stage))
    except TelegramBadRequest:
        pass

    await callback.message.answer(f"📍 Заказ №{order_id} теперь на этапе «{new_stage}».")

    description = _STAGE_DESCRIPTIONS.get(new_stage, "")
    client_text = f"📍 Твой заказ №{order_id} перешёл на этап «{new_stage}»."
    if description:
        client_text += f"\n{description}"
    if is_last:
        client_text += "\n\nЭто финальный этап — работа над заказом завершена 🎉"

    await callback.bot.send_message(order["telegram_user_id"], client_text)
