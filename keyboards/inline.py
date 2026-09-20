"""Инлайн-клавиатуры бота."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню: Проекты / Услуги / Этапы работы / Хочу бриф / Связаться с человеком."""
    buttons = [
        [InlineKeyboardButton(text="📁 Проекты", callback_data="menu:projects")],
        [InlineKeyboardButton(text="🛠 Услуги", callback_data="menu:services")],
        [InlineKeyboardButton(text="🗺 Этапы работы", callback_data="menu:stages")],
        [InlineKeyboardButton(text="📝 Хочу бриф", callback_data="menu:brief")],
        [InlineKeyboardButton(text="🙋 Связаться с человеком", callback_data="menu:contact_human")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def project_list_kb(projects: list[dict]) -> InlineKeyboardMarkup:
    """Список карточек-кейсов (Сценарий 2 паспорта)."""
    buttons = [
        [InlineKeyboardButton(text=p["title"], callback_data=f"projects:card:{p['slug']}")]
        for p in projects
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def project_card_kb(project: dict) -> InlineKeyboardMarkup:
    """Клавиатура под карточкой одного проекта."""
    buttons = [
        [InlineKeyboardButton(text="🔗 Смотреть проект", url=project["url"])],
        [InlineKeyboardButton(text="🙋 Хочу такой же", callback_data="menu:brief")],
        [InlineKeyboardButton(text="⬅️ К списку проектов", callback_data="projects:list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_list_kb(services: list[dict]) -> InlineKeyboardMarkup:
    """Список услуг (Сценарий 3 паспорта)."""
    buttons = [
        [InlineKeyboardButton(text=s["title"], callback_data=f"services:card:{s['slug']}")]
        for s in services
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_card_kb() -> InlineKeyboardMarkup:
    """Клавиатура под описанием одной услуги."""
    buttons = [
        [InlineKeyboardButton(text="✅ Заказать", callback_data="menu:brief")],
        [InlineKeyboardButton(text="⬅️ К списку услуг", callback_data="services:list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def stages_kb() -> InlineKeyboardMarkup:
    """Клавиатура под пояснением этапов работы."""
    buttons = [
        [InlineKeyboardButton(text="📝 Хочу бриф", callback_data="menu:brief")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def brief_project_type_kb(services: list[dict]) -> InlineKeyboardMarkup:
    """Кнопки выбора типа проекта на шаге 2 формы брифа."""
    buttons = [
        [InlineKeyboardButton(text=s["title"], callback_data=f"brief:type:{s['slug']}")]
        for s in services
    ]
    buttons.append([InlineKeyboardButton(text="Другое", callback_data="brief:type:other")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def brief_cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены заполнения формы брифа."""
    buttons = [[InlineKeyboardButton(text="✖️ Отменить", callback_data="brief:cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
