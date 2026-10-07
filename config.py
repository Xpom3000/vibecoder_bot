"""Конфигурация: всё читается из переменных окружения, ничего в коде."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def _env(name: str) -> str:
    value = os.getenv(name)
    return value.strip() if isinstance(value, str) else ""


BOT_TOKEN = _env("BOT_TOKEN")
OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY") or _env("DEEPSEEK_API_KEY")
OPENROUTER_MODEL = _env("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
OPENAI_MODEL = _env("OPENAI_MODEL") or "gpt-4o-mini"
DEEPSEEK_API_KEY = OPENROUTER_API_KEY  # совместимость со старым .env / кодом
ADMIN_CHAT_ID = _env("ADMIN_CHAT_ID")
DATABASE_URL = _env("DATABASE_URL")           # зарезервировано, сейчас используется SQLite

# ЮKassa (тестовый магазин) — онлайн-оплата для заказов с точной числовой
# суммой. Если не задано, бот автоматически использует ручную схему оплаты
# по СБП (see data.portfolio.PAYMENT) — см. services/yookassa.py.
YOOKASSA_SHOP_ID = _env("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = _env("YOOKASSA_SECRET_KEY")

if not BOT_TOKEN:
    sys.exit("BOT_TOKEN не задан. Скопируй .env.example в .env и заполни токен бота.")
