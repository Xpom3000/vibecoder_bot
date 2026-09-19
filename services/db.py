"""Хранение заявок на бриф.

TODO: заменить на подключение к реальной БД, общей с лендингом,
как только будет известна её схема и доступ. Сейчас — временное
локальное хранилище в JSON Lines, чтобы заявки не терялись уже сейчас.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

LEADS_FILE = Path(__file__).resolve().parent.parent / "data" / "leads.jsonl"


def save_lead(lead: dict) -> None:
    """Добавляет одну заявку в конец файла (одна заявка — одна строка JSON)."""
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {**lead, "created_at": datetime.now(timezone.utc).isoformat()}

    with LEADS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
