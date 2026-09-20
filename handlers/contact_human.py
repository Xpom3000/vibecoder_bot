"""Кнопка «Связаться с человеком»: пользователь хочет говорить не с ботом.

По нажатию — владельцу приходит уведомление с именем и username
пользователя, а пользователю бот присылает контакты владельца для связи.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import ADMIN_CHAT_ID
from data.portfolio import CONTACTS
from services.notify import notify_admin

router = Router()


@router.callback_query(F.data == "menu:contact_human")
async def contact_human(callback: CallbackQuery) -> None:
    await callback.answer()

    user = callback.from_user
    username = f"@{user.username}" if user.username else "без username"

    await notify_admin(
        callback.bot,
        ADMIN_CHAT_ID,
        "🙋 Пользователь хочет связаться напрямую:\n"
        f"Имя: {user.full_name}\n"
        f"Username: {username}\n"
        f"id: {user.id}",
    )

    await callback.message.answer(
        "Конечно! Вот мои контакты — пишите напрямую:\n\n"
        f"Telegram: {CONTACTS['telegram']}\n"
        f"Email: {CONTACTS['email']}"
    )
