"""Точка входа. Базовый каркас: реагирует на /start, остальное — заглушки.

ИИ (DeepSeek), база знаний и оплата подключаются позже.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import start


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)

    logging.info("VibeCoder Assistant запущен, ждём /start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
