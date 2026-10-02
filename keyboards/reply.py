"""Постоянное меню под полем ввода (reply-клавиатура).

В отличие от инлайн-кнопок под сообщением, эта клавиатура не привязана к
конкретному сообщению и остаётся на экране у пользователя, пока её явно не
убрать. Отправляется один раз при /start.

По требованиям интерфейса в нижнем меню должно быть ровно четыре кнопки:
Витрина, Корзина, Поддержка, Этапы работы.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_SHOWCASE = "🛍 Витрина"
BTN_CART = "🛒 Корзина"
BTN_CONTACT_HUMAN = "🙋 Поддержка"
BTN_STAGES = "🗺 Этапы работы"

# Сохраняем совместимость со старым кодом и обработчиками, но в постоянном
# меню показываем только четыре кнопки по требованию клиента.
BTN_PROJECTS = "📁 Проекты"
BTN_SERVICES = "🛠 Услуги"
BTN_BRIEF = "📝 Хочу бриф"
BTN_SUPPORT = BTN_CONTACT_HUMAN


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
