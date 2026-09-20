"""Точка входа. Реагирует на /start, показывает проекты, услуги, этапы работы,
витрину, принимает заявку на бриф и отвечает на свободные вопросы через DeepSeek.

Оплата подключается позже.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import brief, contact_human, faq, projects, services, showcase, stages, start
from services.db import init_db


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(projects.router)
    dp.include_router(services.router)
    dp.include_router(stages.router)
    dp.include_router(brief.router)
    dp.include_router(contact_human.router)
    dp.include_router(showcase.router)  # ДО faq.router — кнопки постоянного меню
    dp.include_router(faq.router)  # последним: ловит всё, что не разобрали остальные

    logging.info("VibeCoder Assistant запущен, ждём /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
