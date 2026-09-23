"""Тесты сохранности данных: запись, полное закрытие соединения, повторное
открытие НОВЫМ соединением — имитация перезапуска бота.

Каждая функция в services/db.py и services/cart.py уже открывает и
закрывает своё собственное соединение на вызов (`async with
aiosqlite.connect(...) as db:`), так что "перезапуск" здесь дополнительно
проверяется через отдельное сырое соединение sqlite3 напрямую к файлу на
диске — в обход нашего кода полностью, чтобы доказать, что данные реально
лежат на диске, а не только в памяти процесса.
"""
import sqlite3

from services.cart import add_item, get_cart
from services.db import save_lead

USER = 42


async def test_cart_item_persists_on_disk_across_new_connection(fresh_db):
    await add_item(USER, "landing")

    # "Перезапуск": совсем новое соединение в обход нашего кода.
    raw_conn = sqlite3.connect(fresh_db)
    row = raw_conn.execute(
        "SELECT service_slug, quantity FROM cart_items WHERE telegram_user_id = ?",
        (USER,),
    ).fetchone()
    raw_conn.close()

    assert row == ("landing", 1)


async def test_cart_readable_via_project_code_after_reconnect(fresh_db):
    await add_item(USER, "landing")
    await add_item(USER, "promo")

    # Второй, независимый вызов get_cart() открывает новое соединение
    # (см. docstring файла) — данные должны быть на месте.
    cart = await get_cart(USER)

    assert {line.slug for line in cart} == {"landing", "promo"}


async def test_lead_persists_on_disk_across_new_connection(fresh_db):
    lead = {
        "name": "Тест Тестов",
        "project_type": "Лендинг",
        "task": "Проверка сохранности данных",
        "contact": "+70000000000",
        "telegram_username": "testuser",
        "telegram_user_id": 999,
    }
    await save_lead(lead)

    raw_conn = sqlite3.connect(fresh_db)
    row = raw_conn.execute(
        "SELECT name, task, contact FROM leads WHERE telegram_user_id = 999"
    ).fetchone()
    raw_conn.close()

    assert row == ("Тест Тестов", "Проверка сохранности данных", "+70000000000")


async def test_multiple_writes_all_persist(fresh_db):
    """Несколько последовательных операций (каждая — своё соединение,
    открытое и закрытое) не теряют предыдущие записи."""
    await add_item(USER, "landing")
    await add_item(USER, "promo")
    await add_item(USER, "consultation")

    raw_conn = sqlite3.connect(fresh_db)
    count = raw_conn.execute(
        "SELECT COUNT(*) FROM cart_items WHERE telegram_user_id = ?", (USER,)
    ).fetchone()[0]
    raw_conn.close()

    assert count == 3
