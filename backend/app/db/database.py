"""SQLite connection management and database initialisation."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from app.db.seed import seed_inventory

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(database_path: Path | str) -> sqlite3.Connection:
    # One connection per request; FastAPI may resolve dependencies on a different thread.
    connection = sqlite3.connect(database_path, check_same_thread=False, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(database_path)) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        seed_inventory(connection)
        connection.commit()
