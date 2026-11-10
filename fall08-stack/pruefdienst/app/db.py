"""Dünne Datenbankschicht (psycopg 3, Verbindungspool)."""

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from . import config

_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(config.DATABASE_URL, min_size=1, max_size=8, kwargs={"row_factory": dict_row}, open=True)
    return _pool


def alle(sql: str, params: Any = None) -> list[dict]:
    with pool().connection() as con:
        return list(con.execute(sql, params).fetchall())


def eins(sql: str, params: Any = None) -> dict | None:
    with pool().connection() as con:
        return con.execute(sql, params).fetchone()


def ausfuehren(sql: str, params: Any = None) -> dict | None:
    with pool().connection() as con:
        cur = con.execute(sql, params)
        try:
            return cur.fetchone()
        except Exception:
            return None


def json(wert: Any) -> Jsonb:
    return Jsonb(wert)
