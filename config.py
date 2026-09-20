"""Конфигурация: всё читается из переменных окружения, ничего в коде."""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")   # для свободных вопросов (DeepSeek)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
DATABASE_URL = os.getenv("DATABASE_URL")           # зарезервировано, сейчас используется SQLite

if not BOT_TOKEN:
    sys.exit("BOT_TOKEN не задан. Скопируй .env.example в .env и заполни токен бота.")
