"""Инлайн-клавиатуры бота."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu() -> InlineKeyboardMarkup:
    """Главное меню: Проекты / Услуги / Хочу бриф.

    На этапе базового каркаса кнопки ведут на заглушки —
    реальный функционал появится в handlers/projects.py,
    services.py и brief.py.
    """
    buttons = [
        [InlineKeyboardButton(text="📁 Проекты", callback_data="menu:projects")],
        [InlineKeyboardButton(text="🛠 Услуги", callback_data="menu:services")],
        [InlineKeyboardButton(text="📝 Хочу бриф", callback_data="menu:brief")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
