"""Логика корзины и оформления заказа.

Хранится в той же SQLite БД, что и заявки (services/db.py) — таблицы
cart_items и orders.

Цены в SERVICES (data/portfolio.py) — текстовые строки: "15 000 ₽",
"от 100 000 ₽", "обсуждается индивидуально". Это не готовые числа для
арифметики, поэтому _parse_price() аккуратно достаёт число там, где оно
есть, и отдельно помечает "от"-цены и полностью индивидуальные — чтобы
итоговая сумма в корзине была честной, а не выдуманной.

Корзина хранит только (user_id, slug, количество) — название, описание и
цена всегда берутся из живого SERVICES по slug, а не из снимка на момент
добавления. Так корзина никогда не разойдётся с актуальным прайсом на
витрине. Заказ (orders), наоборот, хранит снимок (items_json) — история
заказа не должна меняться, даже если каталог потом обновится.
"""
import json
import re
from dataclasses import dataclass

import aiosqlite

from data.portfolio import SERVICES, STAGES
from services.db import DB_PATH

CREATE_CART_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL,
    service_slug TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(telegram_user_id, service_slug)
);
"""

CREATE_ORDERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL,
    items_json TEXT NOT NULL,
    total_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ожидает оплаты',
    stage TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_SERVICES_BY_SLUG = {s["slug"]: s for s in SERVICES}

# Порядок этапов — из той же базы знаний, что показывает "Этапы работы"
# (data/portfolio.py), чтобы трекинг и справочный showcase не разошлись.
STAGE_TITLES = [s["title"] for s in STAGES]


async def init_cart_tables() -> None:
    """Создаёт таблицы корзины и заказов, если их ещё нет."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_CART_TABLE_SQL)
        await db.execute(CREATE_ORDERS_TABLE_SQL)
        try:
            # Миграция для БД, созданных до появления трекинга этапов.
            await db.execute("ALTER TABLE orders ADD COLUMN stage TEXT")
        except Exception:
            pass  # столбец уже есть
        await db.commit()


def _parse_price(price_text: str) -> tuple[int | None, bool]:
    """(число_в_рублях, приблизительно). None — если числа в цене нет вовсе
    (например, "обсуждается индивидуально")."""
    is_approx = price_text.strip().lower().startswith("от")
    digits = re.sub(r"[^\d]", "", price_text)
    if not digits:
        return None, False
    return int(digits), is_approx


@dataclass
class CartLine:
    slug: str
    title: str
    price_text: str
    quantity: int
    line_price: int | None  # price * quantity, если цена числовая
    is_approx: bool


async def add_item(user_id: int, slug: str) -> int:
    """Добавляет услугу в корзину; если она там уже есть — увеличивает
    количество вместо дублирования строки (граничный случай: услугу
    добавили дважды). Возвращает итоговое количество этой позиции."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO cart_items (telegram_user_id, service_slug, quantity)
            VALUES (?, ?, 1)
            ON CONFLICT(telegram_user_id, service_slug)
            DO UPDATE SET quantity = quantity + 1
            """,
            (user_id, slug),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT quantity FROM cart_items WHERE telegram_user_id = ? AND service_slug = ?",
            (user_id, slug),
        )
        row = await cursor.fetchone()
        return row[0] if row else 1


async def remove_item(user_id: int, slug: str) -> bool:
    """Удаляет позицию из корзины целиком.

    True — что-то реально удалено. False — позиции уже не было (граничный
    случай: повторное нажатие «Убрать» по той же позиции). Вызывающий код
    не должен считать False ошибкой — это ожидаемая ситуация.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM cart_items WHERE telegram_user_id = ? AND service_slug = ?",
            (user_id, slug),
        )
        await db.commit()
        return cursor.rowcount > 0


async def clear_cart(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart_items WHERE telegram_user_id = ?", (user_id,))
        await db.commit()


async def get_cart(user_id: int) -> list[CartLine]:
    """Содержимое корзины. Название и цена подтягиваются из живого
    SERVICES по slug (не из снимка) — корзина всегда отражает актуальный
    прайс с витрины."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT service_slug, quantity FROM cart_items WHERE telegram_user_id = ? ORDER BY id",
            (user_id,),
        )
        rows = await cursor.fetchall()

    lines: list[CartLine] = []
    for slug, quantity in rows:
        service = _SERVICES_BY_SLUG.get(slug)
        if service is None:
            # Услугу убрали из каталога после того, как её положили в
            # корзину, — молча пропускаем, не показываем то, чего больше нет.
            continue
        price_value, is_approx = _parse_price(service["price"])
        line_price = price_value * quantity if price_value is not None else None
        lines.append(
            CartLine(
                slug=slug,
                title=service["title"],
                price_text=service["price"],
                quantity=quantity,
                line_price=line_price,
                is_approx=is_approx,
            )
        )
    return lines


def format_total(lines: list[CartLine]) -> str:
    """Итоговая сумма человеческим языком, честно отмечая приблизительные
    ("от") и обсуждаемые индивидуально позиции — не выдаём точную цифру там,
    где её на самом деле нет."""
    if not lines:
        return "0 ₽"

    numeric_total = sum(line.line_price for line in lines if line.line_price is not None)
    has_numeric = any(line.line_price is not None for line in lines)
    has_approx = any(line.is_approx for line in lines if line.line_price is not None)
    excluded = [line.title for line in lines if line.line_price is None]

    if not has_numeric:
        # Все позиции без числовой цены — не дублируем "уточняется" и список отдельной строкой.
        return "Стоимость обсуждается индивидуально: " + ", ".join(excluded)

    prefix = "от " if has_approx else ""
    total_str = f"{prefix}{numeric_total:,} ₽".replace(",", " ")

    if excluded:
        total_str += f"\n* Не включено в сумму (цена обсуждается индивидуально): {', '.join(excluded)}"

    return total_str


async def create_order(user_id: int, lines: list[CartLine]) -> int:
    """Создаёт заказ (снимок содержимого корзины) со статусом «ожидает
    оплаты» и очищает корзину. Возвращает id заказа."""
    items_snapshot = [
        {
            "slug": line.slug,
            "title": line.title,
            "price_text": line.price_text,
            "quantity": line.quantity,
        }
        for line in lines
    ]
    total_text = format_total(lines)

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (telegram_user_id, items_json, total_text) VALUES (?, ?, ?)",
            (user_id, json.dumps(items_snapshot, ensure_ascii=False), total_text),
        )
        await db.commit()
        order_id = cursor.lastrowid

    await clear_cart(user_id)
    return order_id


async def get_order(order_id: int) -> dict | None:
    """Заказ по id, в виде словаря (колонки таблицы orders как есть)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
    return dict(row) if row else None


async def set_order_status(order_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def _set_stage(order_id: int, stage: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET stage = ? WHERE id = ?", (stage, order_id))
        await db.commit()


async def set_initial_stage(order_id: int) -> None:
    """Ставит заказ на первый этап («Бриф») — вызывается сразу после
    подтверждения оплаты владельцем."""
    await _set_stage(order_id, STAGE_TITLES[0])


async def advance_order_stage(order_id: int) -> str | None:
    """Переводит заказ на следующий этап. Возвращает новое название этапа
    или None, если заказ не найден, ещё не запущен (нет stage) или уже на
    последнем этапе — двигать дальше некуда (граничный случай)."""
    order = await get_order(order_id)
    if order is None or not order.get("stage"):
        return None
    try:
        idx = STAGE_TITLES.index(order["stage"])
    except ValueError:
        return None
    if idx >= len(STAGE_TITLES) - 1:
        return None  # уже на последнем этапе

    next_stage = STAGE_TITLES[idx + 1]
    await _set_stage(order_id, next_stage)
    return next_stage


async def get_active_order_for_user(user_id: int) -> dict | None:
    """Последний оплаченный заказ пользователя, который ещё не на финальном
    этапе («Передача») — то есть работа по нему ещё идёт. Используется в
    разделе «Этапы работы» для персонального прогресса."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM orders
            WHERE telegram_user_id = ? AND status = 'оплачен'
              AND stage IS NOT NULL AND stage != ?
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, STAGE_TITLES[-1]),
        )
        row = await cursor.fetchone()
    return dict(row) if row else None
