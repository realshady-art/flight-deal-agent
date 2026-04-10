"""SQLite storage: quotes history, notification tracking, run log."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flight_deal_agent.models import DealCandidate, QuoteSnapshot, RunSummary

_SCHEMA = """
CREATE TABLE IF NOT EXISTS quote_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL,
    search_ts     TEXT NOT NULL,
    origin        TEXT NOT NULL,
    destination   TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    return_date   TEXT,
    trip_type     TEXT NOT NULL,
    currency      TEXT NOT NULL,
    total_price   TEXT NOT NULL,
    source        TEXT NOT NULL,
    stops         INTEGER,
    carrier_codes TEXT,
    deep_link     TEXT
);

CREATE TABLE IF NOT EXISTS deal_notifications (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    notified_at   TEXT NOT NULL,
    origin        TEXT NOT NULL,
    destination   TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    return_date   TEXT,
    total_price   TEXT NOT NULL,
    currency      TEXT NOT NULL,
    reason        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL UNIQUE,
    started_at    TEXT NOT NULL,
    finished_at   TEXT NOT NULL,
    task_count    INTEGER NOT NULL,
    api_calls     INTEGER NOT NULL,
    quote_count   INTEGER NOT NULL,
    deal_count    INTEGER NOT NULL,
    errors        TEXT NOT NULL DEFAULT '[]'
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


# -- Quotes ------------------------------------------------------------------

def persist_quotes(db_path: Path, quotes: List[QuoteSnapshot]) -> int:
    if not quotes:
        return 0
    init_db(db_path)
    conn = _connect(db_path)
    try:
        for q in quotes:
            conn.execute(
                """INSERT INTO quote_snapshots
                   (run_id, search_ts, origin, destination, departure_date,
                    return_date, trip_type, currency, total_price, source,
                    stops, carrier_codes, deep_link)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    q.run_id,
                    q.search_ts.isoformat(),
                    q.origin,
                    q.destination,
                    q.departure_date.isoformat(),
                    q.return_date.isoformat() if q.return_date else None,
                    q.trip_type,
                    q.currency,
                    str(q.total_price),
                    q.source,
                    q.stops,
                    json.dumps(q.carrier_codes) if q.carrier_codes else None,
                    q.deep_link,
                ),
            )
        conn.commit()
        return len(quotes)
    finally:
        conn.close()


def get_route_history(
    db_path: Path,
    origin: str,
    destination: str,
    days: int = 30,
) -> List[Decimal]:
    """Return historical total_price values for a route within the last N days."""
    init_db(db_path)
    conn = _connect(db_path)
    try:
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """SELECT total_price FROM quote_snapshots
               WHERE origin=? AND destination=? AND search_ts>=?
               ORDER BY search_ts""",
            (origin, destination, cutoff),
        ).fetchall()
        return [Decimal(r["total_price"]) for r in rows]
    finally:
        conn.close()


def compute_median(prices: List[Decimal]) -> Optional[Decimal]:
    if not prices:
        return None
    s = sorted(prices)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2
    return s[mid]


# -- Notification dedup ------------------------------------------------------

def was_recently_notified(
    db_path: Path,
    origin: str,
    destination: str,
    cooldown_hours: int,
) -> Tuple[bool, Optional[Decimal]]:
    """Check if we already notified for this route within cooldown window.
    Returns (was_notified, last_notified_price)."""
    init_db(db_path)
    conn = _connect(db_path)
    try:
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(hours=cooldown_hours)).isoformat()
        row = conn.execute(
            """SELECT total_price FROM deal_notifications
               WHERE origin=? AND destination=? AND notified_at>=?
               ORDER BY notified_at DESC LIMIT 1""",
            (origin, destination, cutoff),
        ).fetchone()
        if row:
            return True, Decimal(row["total_price"])
        return False, None
    finally:
        conn.close()


def record_notification(db_path: Path, deal: DealCandidate) -> None:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        q = deal.quote
        conn.execute(
            """INSERT INTO deal_notifications
               (notified_at, origin, destination, departure_date, return_date,
                total_price, currency, reason)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                datetime.now(tz=timezone.utc).isoformat(),
                q.origin,
                q.destination,
                q.departure_date.isoformat(),
                q.return_date.isoformat() if q.return_date else None,
                str(q.total_price),
                q.currency,
                deal.reason,
            ),
        )
        conn.commit()
    finally:
        conn.close()


# -- Run log -----------------------------------------------------------------

def log_run(db_path: Path, summary: RunSummary) -> None:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO run_log
               (run_id, started_at, finished_at, task_count, api_calls,
                quote_count, deal_count, errors)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                summary.run_id,
                summary.started_at.isoformat(),
                summary.finished_at.isoformat(),
                summary.task_count,
                summary.api_calls,
                summary.quote_count,
                summary.deal_count,
                json.dumps(summary.errors),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# -- Query helpers (for API / future frontend) -------------------------------

def get_recent_deals(db_path: Path, limit: int = 50) -> List[Dict]:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM deal_notifications ORDER BY notified_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent_quotes(db_path: Path, limit: int = 100) -> List[Dict]:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM quote_snapshots ORDER BY search_ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_run_log(db_path: Path, limit: int = 20) -> List[Dict]:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM run_log ORDER BY finished_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
