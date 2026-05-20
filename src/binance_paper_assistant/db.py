"""SQLite database utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import get_settings


def _sqlite_path(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// URLs are supported in version 1.")
    return database_url[len(prefix) :]


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_path = _sqlite_path(settings.database_url)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    settings = get_settings()
    db_path = Path(_sqlite_path(settings.database_url))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(__file__).with_name("schema.sql")
    with sqlite3.connect(db_path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.commit()

