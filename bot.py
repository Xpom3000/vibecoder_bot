"""Точка входа. Реагирует на /start, показывает проекты, услуги, этапы работы
и принимает заявку на бриф.

ИИ (DeepSeek) и оплата подключаются позже.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import brief, projects, services, stages, start


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(projects.router)
    dp.include_router(services.router)
    dp.include_router(stages.router)
    dp.include_router(brief.router)

    logging.info("VibeCoder Assistant запущен, ждём /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
