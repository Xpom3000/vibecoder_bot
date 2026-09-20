"""Свободные вопросы: база знаний + DeepSeek, с guardrails (паспорт бота +
требования владельца по ограничителям).

Срабатывает на любой текст вне активных сценариев (не команда, не шаг формы
брифа — там текст обрабатывается отдельно в handlers/brief.py по состояниям).
Поэтому роутер должен быть подключён в bot.py последним.

Двухуровневая защита от промпт-инъекций:
1. services.guardrails.is_suspicious() — быстрый keyword-фильтр, срабатывает
   до обращения к ИИ (экономит запрос и надёжнее в лоб).
2. services.ai — инструкции в системном промпте DeepSeek, на случай более
   тонких формулировок, которые фильтр не поймал.

Три исхода из services.ai.ask():
- "answer"   — обычный ответ из базы знаний, показываем как есть.
- "offtopic" — вопрос не про услуги/портфолио VibeCoder или попытка обхода
               инструкций — вежливый отказ сразу, владельца не трогаем.
- "unsure"   — вопрос по теме, но без ответа в базе знаний (или сбой ИИ) —
               честно пересылаем владельцу, а не выдумываем и не молчим.

Память диалога (services/history): в историю попадают только реальные
пары вопрос-ответ ("answer"), чтобы не засорять контекст отказами и
пересланными вопросами — модели это ничем не поможет.
"""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from config import ADMIN_CHAT_ID
from services.ai import OFFTOPIC_REPLY, ask
from services.guardrails import is_suspicious
from services.history import add_message, get_history
from services.notify import notify_admin

router = Router()


@router.message(StateFilter(None), F.text)
async def handle_free_question(message: Message) -> None:
    if is_suspicious(message.text):
        await message.answer(OFFTOPIC_REPLY)
        return

    user_id = message.from_user.id
    history = get_history(user_id)
    kind, text = await ask(message.text, history)

    if kind == "answer":
        add_message(user_id, "user", message.text)
        add_message(user_id, "assistant", text)
        await message.answer(text)
        return

    if kind == "offtopic":
        await message.answer(text)
        return

    # kind == "unsure": вопрос по теме, но нет ответа в базе знаний (или сбой ИИ) —
    # пересылаем владельцу, как требует паспорт, а не отвечаем наугад.
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
