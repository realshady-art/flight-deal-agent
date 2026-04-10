from __future__ import annotations

import sqlite3
from pathlib import Path

from flight_deal_agent.models import QuoteSnapshot


def init_db(db_path: Path) -> None:
    """初始化 SQLite（占位表结构，后续与真实快照字段对齐）。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quote_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_ts TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                return_date TEXT,
                trip_type TEXT NOT NULL,
                currency TEXT NOT NULL,
                total_price TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def persist_quotes(db_path: Path, quotes: list[QuoteSnapshot]) -> int:
    """写入报价快照；返回插入行数。"""
    if not quotes:
        return 0
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        n = 0
        for q in quotes:
            conn.execute(
                """
                INSERT INTO quote_snapshots (
                    search_ts, origin, destination, departure_date,
                    return_date, trip_type, currency, total_price, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    q.search_ts.isoformat(),
                    q.origin,
                    q.destination,
                    q.departure_date.isoformat(),
                    q.return_date.isoformat() if q.return_date else None,
                    q.trip_type,
                    q.currency,
                    str(q.total_price),
                    q.source,
                ),
            )
            n += 1
        conn.commit()
        return n
    finally:
        conn.close()
