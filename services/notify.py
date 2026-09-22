"""Безопасная отправка уведомлений админу.

Сбой отправки (неверный ADMIN_CHAT_ID, админ не начинал диалог с ботом,
бот заблокирован и т.п.) не должен обрывать ответ пользователю — поэтому
ошибка здесь всегда логируется, а не пробрасывается дальше.
"""
import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

logger = logging.getLogger(__name__)


async def notify_admin(
    bot: Bot,
    admin_chat_id: str | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if not admin_chat_id:
        logger.warning("ADMIN_CHAT_ID не задан — уведомление не отправлено: %s", text)
        return

    try:
        await bot.send_message(admin_chat_id, text, reply_markup=reply_markup)
    except Exception:
        logger.exception("Не удалось отправить уведомление админу (ADMIN_CHAT_ID=%s)", admin_chat_id)
