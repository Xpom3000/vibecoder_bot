"""Функция «Этапы работы» из паспорта бота: пять шагов бриф → прототип → дизайн → сборка → передача.

Пока это информационный раздел: показывает все шаги с пояснением.
Отметку «на каком шаге сейчас конкретная заявка» подключим, когда появятся
форма брифа и хранение заявок в БД (Сценарий 4 паспорта).
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from data.portfolio import STAGES
from keyboards.inline import stages_kb

router = Router()


def _render_stages() -> str:
    lines = ["<b>Как строится работа</b>\n"]
    for i, stage in enumerate(STAGES, start=1):
        lines.append(f"{i}. <b>{stage['title']}</b> — {stage['description']}")
    return "\n".join(lines)


@router.callback_query(F.data == "menu:stages")
async def show_stages(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(_render_stages(), reply_markup=stages_kb())
