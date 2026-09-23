"""Общие фикстуры для тестов.

Если в окружении установлена настоящая aiosqlite (как и должно быть —
она в requirements.txt), используется она. Если нет — подставляется
лёгкая асинхронная обёртка поверх стандартного sqlite3 с тем же
интерфейсом (connect/execute/commit/fetchone/fetchall/row_factory),
которого достаточно для services/db.py и services/cart.py. Это не
заглушка бизнес-логики — тестируется реальный код проекта, просто без
внешней зависимости, если её нет под рукой.
"""
import sqlite3
import sys
import types

import pytest


def _install_aiosqlite_shim() -> None:
    if "aiosqlite" in sys.modules:
        return
    try:
        import aiosqlite  # noqa: F401
        return
    except ImportError:
        pass

    class Row(sqlite3.Row):
        pass

    class _Cursor:
        def __init__(self, cursor: sqlite3.Cursor) -> None:
            self._cursor = cursor

        async def fetchone(self):
            return self._cursor.fetchone()

        async def fetchall(self):
            return self._cursor.fetchall()

        @property
        def rowcount(self) -> int:
            return self._cursor.rowcount

        @property
        def lastrowid(self):
            return self._cursor.lastrowid

    class _Connection:
        def __init__(self, conn: sqlite3.Connection) -> None:
            self._conn = conn
            self.row_factory = None

        async def execute(self, sql: str, params=()):
            if self.row_factory is not None:
                self._conn.row_factory = self.row_factory
            cur = self._conn.execute(sql, params)
            return _Cursor(cur)

        async def commit(self) -> None:
            self._conn.commit()

        async def close(self) -> None:
            self._conn.close()

        async def __aenter__(self) -> "_Connection":
            return self

        async def __aexit__(self, *exc) -> None:
            self._conn.close()

    def connect(path):
        return _Connection(sqlite3.connect(str(path)))

    shim = types.ModuleType("aiosqlite")
    shim.connect = connect
    shim.Row = Row
    sys.modules["aiosqlite"] = shim


_install_aiosqlite_shim()


@pytest.fixture
async def fresh_db(tmp_path, monkeypatch):
    """Изолированная БД на каждый тест: свежий временный файл, реальные
    init_db()/init_cart_tables() из проекта. Возвращает путь к файлу — по
    нему в тестах можно открыть отдельное «сырое» соединение и убедиться,
    что данные реально легли на диск (тесты сохранности)."""
    import services.cart as cart_module
    import services.db as db_module

    test_db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", test_db_path)
    monkeypatch.setattr(cart_module, "DB_PATH", test_db_path)

    await db_module.init_db()
    await cart_module.init_cart_tables()

    return test_db_path
