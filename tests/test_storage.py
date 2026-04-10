from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import List

from flight_deal_agent.models import DealCandidate, QuoteSnapshot, RunSummary
from flight_deal_agent.storage import (
    compute_median,
    get_recent_deals,
    get_recent_quotes,
    get_route_history,
    get_run_log,
    init_db,
    log_run,
    persist_quotes,
    record_notification,
    was_recently_notified,
)


def test_init_db_creates_tables(tmp_db: Path):
    init_db(tmp_db)
    assert tmp_db.exists()


def test_persist_and_retrieve_quotes(tmp_db: Path, sample_quotes: List[QuoteSnapshot]):
    init_db(tmp_db)
    n = persist_quotes(tmp_db, sample_quotes)
    assert n == 3
    rows = get_recent_quotes(tmp_db, limit=10)
    assert len(rows) == 3


def test_route_history(tmp_db: Path, sample_quotes: List[QuoteSnapshot]):
    init_db(tmp_db)
    persist_quotes(tmp_db, sample_quotes)
    history = get_route_history(tmp_db, "BOS", "LHR")
    assert len(history) == 1
    assert history[0] == Decimal("800")


def test_compute_median_odd():
    assert compute_median([Decimal("1"), Decimal("3"), Decimal("5")]) == Decimal("3")


def test_compute_median_even():
    assert compute_median([Decimal("1"), Decimal("3")]) == Decimal("2")


def test_compute_median_empty():
    assert compute_median([]) is None


def test_notification_cooldown(tmp_db: Path, sample_quotes: List[QuoteSnapshot]):
    init_db(tmp_db)
    notified, _ = was_recently_notified(tmp_db, "BOS", "LHR", 24)
    assert notified is False

    deal = DealCandidate(quote=sample_quotes[0], reason="test")
    record_notification(tmp_db, deal)

    notified, price = was_recently_notified(tmp_db, "BOS", "LHR", 24)
    assert notified is True
    assert price == Decimal("800")


def test_log_run(tmp_db: Path):
    init_db(tmp_db)
    now = datetime.now(tz=timezone.utc)
    summary = RunSummary(
        run_id="test123", started_at=now, finished_at=now,
        task_count=5, api_calls=3, quote_count=10, deal_count=2,
    )
    log_run(tmp_db, summary)
    rows = get_run_log(tmp_db)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "test123"


def test_recent_deals_empty(tmp_db: Path):
    init_db(tmp_db)
    assert get_recent_deals(tmp_db) == []
