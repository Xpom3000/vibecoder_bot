"""Сценарий 1 (паспорт бота): /start, в том числе с параметром start=landing."""
from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.inline import main_menu
from keyboards.reply import persistent_menu
from services.history import clear_history

router = Router()


async def _finish_state(state: FSMContext) -> None:
    """Compatibility wrapper: try `finish()`, fall back to `clear()` if needed."""
    if hasattr(state, "finish"):
        await state.clear()
        return
    if hasattr(state, "clear"):
        await state.clear()
        return
    try:
        await state.set_state(None)
    except Exception:
        return

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

MENU_HINT = "Меню всегда под рукой внизу экрана 👇"


@router.message(CommandStart(deep_link=True))
async def start_with_param(message: Message, command: CommandObject, state: FSMContext) -> None:
    """/start с параметром, например t.me/vibecoder_bot?start=landing."""
    clear_history(message.from_user.id)  # новый разговор — чистый контекст
    await state.clear()
    payload = command.args
    text = GREETING_LANDING if payload == "landing" else GREETING_DEFAULT
    await message.answer(text, reply_markup=main_menu())
    # Reply-клавиатуру нельзя прикрепить к тому же сообщению, что и инлайн-меню —
    # у Telegram-сообщения только один reply_markup, поэтому отдельным сообщением.
    await message.answer(MENU_HINT, reply_markup=persistent_menu())


@router.message(CommandStart())
async def start_default(message: Message, state: FSMContext) -> None:
    """Обычный /start без параметров."""
    clear_history(message.from_user.id)  # новый разговор — чистый контекст
    await message.answer(GREETING_DEFAULT, reply_markup=main_menu())
    await message.answer(MENU_HINT, reply_markup=persistent_menu())


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возврат в главное меню из любого раздела."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(GREETING_DEFAULT, reply_markup=main_menu())
