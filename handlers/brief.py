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
from keyboards.reply import BTN_BRIEF, BTN_CART, BTN_CONTACT_HUMAN, BTN_SHOWCASE
from services.db import save_lead
from states.brief import BriefForm

router = Router()


async def _reset_state(state) -> None:
    """Совместимый сброс состояния для реального FSMContext и моков в тестах."""
    clear = getattr(state, "clear", None)
    if callable(clear):
        await clear()
        return

    finish = getattr(state, "finish", None)
    if callable(finish):
        await finish()


PROJECT_TYPE_TITLES = {s["slug"]: s["title"] for s in SERVICES}
PROJECT_TYPE_TITLES["other"] = "Другое"

_BRIEF_STATES = (BriefForm.name, BriefForm.project_type, BriefForm.task, BriefForm.contact)
_RESERVED_MENU_TEXTS = {BTN_SHOWCASE, BTN_CART, BTN_CONTACT_HUMAN}


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


@router.message(F.text == BTN_BRIEF)
async def start_brief_from_message(message: Message, state: FSMContext) -> None:
    await state.set_state(BriefForm.name)
    await message.answer(
        "Начнём 📝 Как к тебе обращаться?",
        reply_markup=brief_cancel_kb(),
    )


@router.callback_query(F.data == "menu:brief")
async def start_brief(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(BriefForm.name)
    await callback.message.answer(
        "Начнём 📝 Как к тебе обращаться?",
        reply_markup=brief_cancel_kb(),
    )


@router.callback_query(F.data == "brief:cancel")
async def cancel_brief(callback: CallbackQuery, state: FSMContext) -> None:
    await _reset_state(state)
    await callback.answer("Заявка отменена")
    await callback.message.answer("Хорошо, вернёмся в любое время 🙂", reply_markup=main_menu())


@router.message(StateFilter(*_BRIEF_STATES), F.text == BTN_SHOWCASE)
async def leave_brief_for_showcase(message: Message, state: FSMContext) -> None:
    """Пользователь нажал «Витрина» посреди незавершённой формы брифа —
    тихо отменяем форму (он не нажимал «Отменить» явно) и сразу показываем
    то, что он запросил, а не проглатываем нажатие как текстовый ответ."""
    await _reset_state(state)
    from handlers.showcase import show_showcase

    await show_showcase(message)


@router.message(StateFilter(*_BRIEF_STATES), F.text == BTN_CART)
async def leave_brief_for_cart(message: Message, state: FSMContext) -> None:
    await _reset_state(state)
    from handlers.cart import show_cart

    await show_cart(message)


@router.message(StateFilter(*_BRIEF_STATES), F.text == BTN_CONTACT_HUMAN)
async def leave_brief_for_contact(message: Message, state: FSMContext) -> None:
    await _reset_state(state)
    from handlers.contact_human import contact_human_message

    await contact_human_message(message)


@router.message(StateFilter(BriefForm.name), ~F.text.in_(_RESERVED_MENU_TEXTS))
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
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


@router.message(StateFilter(BriefForm.task), ~F.text.in_(_RESERVED_MENU_TEXTS))
async def process_task(message: Message, state: FSMContext) -> None:
    await state.update_data(task=message.text)
    await state.set_state(BriefForm.contact)
    await message.answer(
        "И последнее — оставь телефон или email, чтобы можно было связаться.",
        reply_markup=brief_cancel_kb(),
    )


@router.message(StateFilter(BriefForm.contact), ~F.text.in_(_RESERVED_MENU_TEXTS))
async def process_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.text)
    data = await state.get_data()
    await _reset_state(state)

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
