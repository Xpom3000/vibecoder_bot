"""Функция «Этапы работы» из паспорта бота: пять шагов бриф → прототип →
дизайн → сборка → передача.

Реальный трекинг: если у пользователя есть свой оплаченный заказ, который
ещё не на финальном этапе, показываем персональный прогресс — с отметкой
текущего шага — вместо общего справочного списка. Если активного заказа
нет, показываем общий showcase, как и раньше.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from data.portfolio import STAGES
from keyboards.inline import stages_kb
from services.cart import STAGE_TITLES, get_active_order_for_user

router = Router()


def _render_stages_generic() -> str:
    lines = ["<b>Как строится работа</b>\n"]
    for i, stage in enumerate(STAGES, start=1):
        lines.append(f"{i}. <b>{stage['title']}</b> — {stage['description']}")
    return "\n".join(lines)


def _render_stages_for_order(order: dict) -> str:
    current_idx = STAGE_TITLES.index(order["stage"])
    lines = [f"<b>Прогресс по заказу №{order['id']}</b>\n"]
    for i, stage in enumerate(STAGES, start=1):
        idx = i - 1
        if idx < current_idx:
            mark = "✅"
        elif idx == current_idx:
            mark = "🔵"
        else:
            mark = "⬜"
        lines.append(f"{mark} {i}. <b>{stage['title']}</b> — {stage['description']}")
    lines.append(f"\nСейчас на этапе: <b>{order['stage']}</b>")
    return "\n".join(lines)


@router.callback_query(F.data == "menu:stages")
async def show_stages(callback: CallbackQuery) -> None:
    await callback.answer()

    active_order = await get_active_order_for_user(callback.from_user.id)

    if active_order is not None:
        text = _render_stages_for_order(active_order)
    else:
        text = _render_stages_generic()

    await callback.message.answer(text, reply_markup=stages_kb())
