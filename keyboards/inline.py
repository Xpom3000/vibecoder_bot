"""Инлайн-клавиатуры бота."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню: Проекты / Услуги / Этапы работы / Хочу бриф / Поддержка."""
    buttons = [
        [InlineKeyboardButton(text="📁 Проекты", callback_data="menu:projects")],
        [InlineKeyboardButton(text="🛠 Услуги", callback_data="menu:services")],
        [InlineKeyboardButton(text="🗺 Этапы работы", callback_data="menu:stages")],
        [InlineKeyboardButton(text="📝 Хочу бриф", callback_data="menu:brief")],
        [InlineKeyboardButton(text="🙋 Поддержка", callback_data="menu:contact_human")],
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
        [InlineKeyboardButton(text="🙋 Хочу такой же", callback_data=f"menu:brief:{project['slug']}")],
        [InlineKeyboardButton(text="⬅️ К списку проектов", callback_data="projects:list")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_list_kb(services: list[dict]) -> InlineKeyboardMarkup:
    """Список услуг (Сценарий 3 паспорта). По 2 кнопки в ряд — с расширением
    ассортимента список стал длиннее, в один столбец было бы неудобно."""
    buttons = []
    for i in range(0, len(services), 2):
        row = [
            InlineKeyboardButton(text=s["title"], callback_data=f"services:card:{s['slug']}")
            for s in services[i : i + 2]
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def service_card_kb(slug: str) -> InlineKeyboardMarkup:
    """Клавиатура под описанием одной услуги. Передаёт slug услуги при заказе."""
    buttons = [
        [InlineKeyboardButton(text="✅ Заказать", callback_data=f"menu:brief:{slug}")],
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
    """Кнопки выбора типа проекта на шаге 2 формы брифа. По 2 в ряд —
    список услуг расширился, одной колонкой было бы слишком длинно."""
    buttons = []
    for i in range(0, len(services), 2):
        row = [
            InlineKeyboardButton(text=s["title"], callback_data=f"brief:type:{s['slug']}")
            for s in services[i : i + 2]
        ]
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="Другое", callback_data="brief:type:other")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def brief_cancel_kb() -> InlineKeyboardMarkup:
    """Кнопка отмены заполнения формы брифа."""
    buttons = [[InlineKeyboardButton(text="✖️ Отменить", callback_data="brief:cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def add_to_cart_kb(slug: str) -> InlineKeyboardMarkup:
    """Кнопка под карточкой услуги в витрине (handlers/showcase.py)."""
    buttons = [[InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"cart:add:{slug}")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_kb(lines: list) -> InlineKeyboardMarkup:
    """Клавиатура под сообщением с корзиной: «Убрать» под каждой позицией
    и «Оформить заказ» общей кнопкой внизу (handlers/cart.py)."""
    buttons = [
        [InlineKeyboardButton(text=f"❌ Убрать «{line.title}»", callback_data=f"cart:remove:{line.slug}")]
        for line in lines
    ]
    buttons.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="cart:checkout")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_payment_kb(order_id: int) -> InlineKeyboardMarkup:
    """Кнопка клиента «Я оплатил(а)» под инструкцией по оплате (handlers/payment.py)."""
    buttons = [[InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data=f"order:paid:{order_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_confirm_payment_kb(order_id: int) -> InlineKeyboardMarkup:
    """Кнопка владельца «Подтвердить оплату» — приходит только в его личном
    чате с ботом (handlers/payment.py), больше никто её не увидит."""
    buttons = [[InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"order:confirm:{order_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_advance_stage_kb(order_id: int, current_stage: str) -> InlineKeyboardMarkup:
    """Кнопка владельца «Следующий этап» — видна только в его личном чате
    (handlers/tracking.py). Владелец двигает заказ вручную по факту
    реального прогресса, а не по таймеру."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"➡️ Следующий этап (сейчас: {current_stage})",
                callback_data=f"order:advance:{order_id}",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
