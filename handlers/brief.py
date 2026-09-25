"""Сценарий 4 (паспорт бота): пошаговая заявка на бриф.

Шаги: имя → тип проекта (кнопки) → описание задачи → контакт.
По завершении: заявка сохраняется (services/db.py) и админу
приходит карточка с данными.
"""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_CHAT_ID
from services.notify import notify_admin
from data.portfolio import SERVICES
from keyboards.inline import brief_cancel_kb, brief_project_type_kb, main_menu
from services.db import save_lead
from states.brief import BriefForm

router = Router()

PROJECT_TYPE_TITLES = {s["slug"]: s["title"] for s in SERVICES}
PROJECT_TYPE_TITLES["other"] = "Другое"


def _admin_card(data: dict, username: str | None) -> str:
    contact_line = data["contact"]
    if username:
        contact_line = f"@{username} / {contact_line}"

    return (
        "🆕 Новая заявка на бриф\n"
        f"Имя: {data['name']}\n"
        f"Тип: {data['project_type']}\n"
        f"Задача: {data['task']}\n"
        f"Контакт: {contact_line}\n"
        "Источник: bot"
    )


@router.callback_query(F.data.startswith("menu:brief"))
async def start_brief(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    # Обрабатываем форму вызова: menu:brief or menu:brief:slug
    parts = callback.data.split(":")
    if len(parts) > 2:
        slug = parts[-1]
        title = PROJECT_TYPE_TITLES.get(slug)
        if title:
            await state.update_data(project_type=title)

    await state.set_state(BriefForm.name)
    await callback.message.answer(
        "Начнём 📝 Как к тебе обращаться?",
        reply_markup=brief_cancel_kb(),
    )


@router.callback_query(F.data == "brief:cancel")
async def cancel_brief(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Заявка отменена")
    await callback.message.answer("Хорошо, вернёмся в любое время 🙂", reply_markup=main_menu())


@router.message(StateFilter(BriefForm.name))
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    data = await state.get_data()

    # Если тип проекта уже предзаполнен (например, из карточки услуги),
    # пропускаем шаг выбора типа и идём сразу к описанию задачи.
    if data.get("project_type"):
        await state.set_state(BriefForm.task)
        await message.answer(
            "Расскажи в двух-трёх предложениях, какая задача — что должен делать сайт "
            "и для кого он.",
            reply_markup=brief_cancel_kb(),
        )
        return

    await state.set_state(BriefForm.project_type)
    await message.answer(
        "Какой тип проекта интересует?",
        reply_markup=brief_project_type_kb(SERVICES),
    )


@router.callback_query(StateFilter(BriefForm.project_type), F.data.startswith("brief:type:"))
async def process_project_type(callback: CallbackQuery, state: FSMContext) -> None:
    slug = callback.data.split(":")[-1]
    title = PROJECT_TYPE_TITLES.get(slug, slug)

    await state.update_data(project_type=title)
    await state.set_state(BriefForm.task)

    await callback.answer()
    await callback.message.answer(
        "Расскажи в двух-трёх предложениях, какая задача — что должен делать сайт "
        "и для кого он.",
        reply_markup=brief_cancel_kb(),
    )


@router.message(StateFilter(BriefForm.task))
async def process_task(message: Message, state: FSMContext) -> None:
    await state.update_data(task=message.text)
    await state.set_state(BriefForm.contact)
    await message.answer(
        "И последнее — оставь телефон или email, чтобы можно было связаться.",
        reply_markup=brief_cancel_kb(),
    )


@router.message(StateFilter(BriefForm.contact))
async def process_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.text)
    data = await state.get_data()
    from handlers.start import _finish_state

    await _finish_state(state)

    await save_lead(
        {
            "name": data["name"],
            "project_type": data["project_type"],
            "task": data["task"],
            "contact": data["contact"],
            "telegram_username": message.from_user.username,
            "telegram_user_id": message.from_user.id,
        }
    )

    # Сбой отправки уведомления не должен помешать пользователю получить подтверждение.
    await notify_admin(message.bot, ADMIN_CHAT_ID, _admin_card(data, message.from_user.username))

    await message.answer(
        "Заявка принята ✅ Скоро с тобой свяжутся. Спасибо!",
        reply_markup=main_menu(),
    )
