"""Клиент DeepSeek для ответов на свободные вопросы (раздел FAQ, паспорт бота).

Правило из паспорта: бот не выдумывает ответы. Модель отвечает только на
основе базы знаний ниже; если вопрос выходит за её рамки или модель не
уверена — код возвращает None, и handlers/faq.py пересылает вопрос владельцу.
"""
import logging

import aiohttp

from config import DEEPSEEK_API_KEY
from data.portfolio import PROJECTS, SERVICES, STAGES

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"  # deepseek-chat устарела 24.07.2026, актуальная замена — v4-flash
UNSURE_MARKER = "UNSURE"
REQUEST_TIMEOUT = 20

logger = logging.getLogger(__name__)


def _build_knowledge_base() -> str:
    parts = ["ПРОЕКТЫ:"]
    for p in PROJECTS:
        parts.append(
            f"- {p['title']} ({p['subtitle']}). "
            f"Задача: {p['task'] or 'не указана'}. "
            f"Стек: {p['stack'] or 'не указан'}. "
            f"Особенности: {p['features'] or 'не указаны'}. "
            f"Результат: {p['result'] or 'не указан'}."
        )

    parts.append("\nУСЛУГИ:")
    for s in SERVICES:
        parts.append(f"- {s['title']}: {s['description']}")

    parts.append("\nЭТАПЫ РАБОТЫ:")
    for i, stage in enumerate(STAGES, start=1):
        parts.append(f"{i}. {stage['title']} — {stage['description']}")

    return "\n".join(parts)


def _system_prompt() -> str:
    return (
        "Ты — VibeCoder Assistant, бот-консультант по портфолио веб-студии VibeCoder. "
        "Отвечай кратко, по делу, на русском языке, дружелюбно и без канцелярита.\n\n"
        "У тебя есть база знаний ниже. Отвечай ТОЛЬКО на основе неё. "
        "Категорически нельзя придумывать факты о проектах, ценах, сроках "
        "или технологиях, которых нет в базе знаний.\n\n"
        "Если вопрос выходит за рамки базы знаний, требует точных цифр "
        "(конкретная цена, срок, договор) или ты не уверен в ответе — "
        f"ответь ровно одним словом без пояснений: {UNSURE_MARKER}\n\n"
        "База знаний:\n" + _build_knowledge_base()
    )


async def ask(question: str) -> str | None:
    """Возвращает ответ модели или None, если модель не уверена / произошла ошибка.

    None — сигнал вызывающему коду переслать вопрос владельцу.
    """
    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY не задан — свободные вопросы не обрабатываются.")
        return None

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("DeepSeek API error %s: %s", resp.status, body)
                    return None
                data = await resp.json()
    except Exception:
        logger.exception("Не удалось получить ответ от DeepSeek")
        return None

    try:
        answer = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        logger.error("Неожиданный формат ответа DeepSeek: %s", data)
        return None

    if not answer or answer.upper().startswith(UNSURE_MARKER):
        return None

    return answer
