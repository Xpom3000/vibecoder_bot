"""Свободные вопросы: база знаний + DeepSeek, фолбэк на владельца (паспорт бота).

Срабатывает на любой текст вне активных сценариев (не команда, не шаг формы
брифа — там текст обрабатывается отдельно в handlers/brief.py по состояниям).
Поэтому роутер должен быть подключён в bot.py последним.
"""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from config import ADMIN_CHAT_ID
from services.ai import ask
from services.notify import notify_admin

router = Router()


@router.message(StateFilter(None), F.text)
async def handle_free_question(message: Message) -> None:
    answer = await ask(message.text)

    if answer is not None:
        await message.answer(answer)
        return

    # ИИ не уверен или недоступен — пересылаем вопрос владельцу, как требует паспорт,
    # а не отвечаем наугад. Сбой пересылки не должен оставить пользователя без ответа.
    who = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name
    await notify_admin(
        message.bot,
        ADMIN_CHAT_ID,
        "🤔 Бот не смог уверенно ответить на вопрос:\n"
        f"«{message.text}»\n\n"
        f"От: {who} (id {message.from_user.id})",
    )

    await message.answer(
        "Хороший вопрос! Не хочу гадать — переслал его владельцу, он ответит лично 🙂"
    )
