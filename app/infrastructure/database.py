"""Acesso simples ao SQLite.

Usamos sqlite3 da biblioteca padrão para manter o projeto leve.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from app.config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    component_version TEXT NOT NULL,
    component_type TEXT NOT NULL,
    score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    summary_line TEXT NOT NULL,
    justification TEXT NOT NULL,
    criteria_scores_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def initialize_database() -> None:
    # Cria a tabela principal se ela ainda não existir.
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(SCHEMA)
        conn.commit()


@contextmanager
def get_connection():
    # Fecha a conexão mesmo se algo falhar.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
