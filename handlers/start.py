"""Сценарий 1 (паспорт бота): /start, в том числе с параметром start=landing."""
from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from keyboards.inline import main_menu

router = Router()

GREETING_LANDING = (
    "Привет! Ты с лендинга VibeCoder 👋\n"
    "Могу показать проекты, рассказать про услуги или сразу записать на бриф. "
    "Что интересует?"
)

GREETING_DEFAULT = (
    "Привет! Я — VibeCoder Assistant, бот-консультант по портфолио VibeCoder 👋\n"
    "Могу показать проекты, рассказать про услуги или сразу записать на бриф. "
    "Что интересует?"
)


@router.message(CommandStart(deep_link=True))
async def start_with_param(message: Message, command: CommandObject) -> None:
    """/start с параметром, например t.me/vibecoder_bot?start=landing."""
    payload = command.args

    if payload == "landing":
        text = GREETING_LANDING
    else:
        # Неизвестный параметр — показываем стандартное приветствие,
        # но не теряем пользователя.
        text = GREETING_DEFAULT

    await message.answer(text, reply_markup=main_menu())


@router.message(CommandStart())
async def start_default(message: Message) -> None:
    """Обычный /start без параметров."""
    await message.answer(GREETING_DEFAULT, reply_markup=main_menu())


@router.callback_query(F.data == "menu:projects")
async def on_projects_stub(callback: CallbackQuery) -> None:
    # TODO: заменить на handlers/projects.py (Сценарий 2 паспорта)
    await callback.answer()
    await callback.message.answer("Раздел «Проекты» скоро будет 🙂")


@router.callback_query(F.data == "menu:services")
async def on_services_stub(callback: CallbackQuery) -> None:
    # TODO: заменить на handlers/services.py (Сценарий 3 паспорта)
    await callback.answer()
    await callback.message.answer("Раздел «Услуги» скоро будет 🙂")


@router.callback_query(F.data == "menu:brief")
async def on_brief_stub(callback: CallbackQuery) -> None:
    # TODO: заменить на handlers/brief.py (Сценарий 4 паспорта)
    await callback.answer()
    await callback.message.answer("Форма заявки на бриф скоро будет 🙂")
