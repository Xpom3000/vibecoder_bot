"""Безопасная отправка уведомлений админу.

Сбой отправки (неверный ADMIN_CHAT_ID, админ не начинал диалог с ботом,
бот заблокирован и т.п.) не должен обрывать ответ пользователю — поэтому
ошибка здесь всегда логируется, а не пробрасывается дальше.
"""
import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


async def notify_admin(bot: Bot, admin_chat_id: str | None, text: str) -> None:
    if not admin_chat_id:
        logger.warning("ADMIN_CHAT_ID не задан — уведомление не отправлено: %s", text)
        return

    try:
        await bot.send_message(admin_chat_id, text)
    except Exception:
        logger.exception("Не удалось отправить уведомление админу (ADMIN_CHAT_ID=%s)", admin_chat_id)
