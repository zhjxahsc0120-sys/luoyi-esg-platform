from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pymysql
from pymysql.cursors import DictCursor


def _load_local_env() -> None:
    """Load the project-local .env without overriding an explicit process env."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


MYSQL_CONFIG = {
    "host": os.getenv("LUOYI_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("LUOYI_MYSQL_PORT", "3307")),
    "user": os.getenv("LUOYI_MYSQL_USER", "luoyi_app"),
    "password": os.getenv("LUOYI_MYSQL_PASSWORD", ""),
    "database": os.getenv("LUOYI_MYSQL_DATABASE", "luoyi_esg"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 3,
    "read_timeout": 10,
    "write_timeout": 10,
}


def mysql_enabled() -> bool:
    return os.getenv("LUOYI_DB_MODE", "mysql").lower() in {"mysql", "auto"}


@contextmanager
def mysql_connect() -> Iterator[pymysql.connections.Connection]:
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def mysql_ping() -> dict:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS version, DATABASE() AS database_name")
            row = cur.fetchone()
    return {
        "ok": True,
        "engine": "mysql",
        "host": MYSQL_CONFIG["host"],
        "port": MYSQL_CONFIG["port"],
        "database": row["database_name"],
        "version": row["version"],
    }
