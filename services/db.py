"""Хранение заявок на бриф — реальная БД бота (SQLite), как рекомендует
паспорт для MVP-этапа.

Лендинг сейчас статический HTML/CSS/JS без бэкенда — делить с ним БД
буквально нечего. Поэтому это отдельная, но настоящая база: данные не
теряются между перезапусками бота и их легко смотреть/выгружать
(например, DB Browser for SQLite). Если у лендинга позже появится
бэкенд — эти же данные можно будет читать напрямую из файла БД или
перенести на PostgreSQL, схема останется той же.
"""
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vibecoder_bot.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    project_type TEXT NOT NULL,
    task TEXT,
    contact TEXT NOT NULL,
    telegram_username TEXT,
    telegram_user_id INTEGER,
    source TEXT NOT NULL DEFAULT 'bot',
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

INSERT_LEAD_SQL = """
INSERT INTO leads (name, project_type, task, contact, telegram_username, telegram_user_id)
VALUES (:name, :project_type, :task, :contact, :telegram_username, :telegram_user_id)
"""


async def init_db() -> None:
    """Создаёт файл БД и таблицу, если их ещё нет. Вызывается один раз при старте бота."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


async def save_lead(lead: dict) -> None:
    """Сохраняет одну заявку на бриф."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(INSERT_LEAD_SQL, lead)
        await db.commit()
