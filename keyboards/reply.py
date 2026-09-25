"""Постоянное меню под полем ввода (reply-клавиатура).

В отличие от инлайн-кнопок под сообщением, эта клавиатура не привязана к
конкретному сообщению и остаётся на экране у пользователя, пока её явно не
убрать. Отправляется один раз при /start.

Нажатие такой кнопки в Telegram — это обычное текстовое сообщение с текстом
кнопки, а не callback_query. Поэтому хендлеры на эти кнопки (handlers/showcase.py,
handlers/contact_human.py) обязательно должны быть подключены в bot.py
раньше handlers/faq.py — иначе кнопки перехватит catch-all для свободных
вопросов к ИИ.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_SHOWCASE = "🛍 Витрина"
BTN_CART = "🛒 Корзина"
BTN_CONTACT_HUMAN = "🙋 Поддержка"
BTN_STAGES = "🗺 Этапы работы"


def persistent_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=BTN_SHOWCASE),
            KeyboardButton(text=BTN_CART),
        ],
        [
            KeyboardButton(text=BTN_CONTACT_HUMAN),
            KeyboardButton(text=BTN_STAGES),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
