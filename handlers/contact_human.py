"""Поддержка: доступна и из инлайн-карточки, и из постоянного меню
(keyboards/reply.py) — по нажатию одно и то же поведение.

Владельцу приходит уведомление с именем и username пользователя, а
пользователю бот присылает контакты владельца для связи.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, User
from typing import Awaitable, Callable

from config import ADMIN_CHAT_ID
from data.portfolio import CONTACTS
from keyboards.reply import BTN_CONTACT_HUMAN
from services.notify import notify_admin

router = Router()


async def _handle_contact_human(bot, user: User, answer: Callable[[str], Awaitable[None]]) -> None:
    """Общая логика для инлайн-кнопки и кнопки постоянного меню."""
    username = f"@{user.username}" if user.username else "без username"

    await notify_admin(
        bot,
        ADMIN_CHAT_ID,
        "🙋 Пользователь хочет связаться напрямую:\n"
        f"Имя: {user.full_name}\n"
        f"Username: {username}\n"
        f"id: {user.id}",
    )

    await answer(
        "Конечно! Вот мои контакты — пишите напрямую:\n\n"
        f"Telegram: {CONTACTS['telegram']}\n"
        f"Email: {CONTACTS['email']}"
    )


@router.callback_query(F.data == "menu:contact_human")
async def contact_human_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    await _handle_contact_human(callback.bot, callback.from_user, callback.message.answer)


@router.message(lambda message: (message.text or "").strip() in {
    BTN_CONTACT_HUMAN,
    "Поддержка",
})
async def contact_human_message(message: Message) -> None:
    await _handle_contact_human(message.bot, message.from_user, message.answer)
