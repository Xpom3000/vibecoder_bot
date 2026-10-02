"""Сценарий 2 (паспорт бота): каталог проектов и карточки кейсов."""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from data.portfolio import PROJECTS
from keyboards.inline import project_card_kb, project_list_kb

router = Router()

LIST_TEXT = "Вот три последних кейса. Жми на карточку, чтобы посмотреть детали 👇"


def _find_project(slug: str) -> dict | None:
    return next((p for p in PROJECTS if p["slug"] == slug), None)


def _render_card(project: dict) -> str:
    task = project["task"] or "уточняется"
    stack = project["stack"] or "уточняется"
    features = project["features"] or "уточняется"
    result = project["result"] or "уточняется"
    return (
        f"<b>{project['title']}</b> — {project['subtitle']}\n\n"
        f"📌 Задача: {task}\n"
        f"🛠 Стек: {stack}\n"
        f"✨ Особенности: {features}\n"
        f"📈 Результат: {result}"
    )


@router.callback_query(F.data == "menu:projects")
async def show_project_list(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(LIST_TEXT, reply_markup=project_list_kb(PROJECTS))


@router.callback_query(F.data == "projects:list")
async def back_to_list(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(LIST_TEXT, reply_markup=project_list_kb(PROJECTS))


@router.callback_query(F.data.startswith("projects:card:"))
async def show_project_card(callback: CallbackQuery) -> None:
    slug = callback.data.split(":")[-1]
    project = _find_project(slug)

    await callback.answer()

    if project is None:
        await callback.message.answer("Такой проект не нашёлся 🤔")
        return

    await callback.message.edit_text(_render_card(project), reply_markup=project_card_kb(project))
