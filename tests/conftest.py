from __future__ import annotations

import textwrap
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import List

import pytest
import yaml

from flight_deal_agent.models import QuoteSnapshot


@pytest.fixture()
def tmp_config(tmp_path: Path) -> Path:
    cfg = {
        "app": {"name": "test", "timezone": "UTC"},
        "origin_airports": ["BOS"],
        "target_region_id": "test_region",
        "trip": {
            "type": "round_trip",
            "date_window": {
                "min_days_ahead": 7,
                "max_days_ahead": 28,
                "sample_every_n_days": 14,
                "min_trip_nights": 5,
                "max_trip_nights": 10,
                "trip_night_samples": [5, 7],
            },
        },
        "currency": "USD",
        "collector": {"provider": "stub", "request_budget_per_run": 10},
        "amadeus": {"test_mode": True},
        "storage": {"sqlite_path": str(tmp_path / "test.db")},
        "alerts": {
            "channel": "stdout",
            "cooldown_hours": 24,
            "renotify_price_drop_pct": 8,
        },
        "thresholds": {"max_total_price": 5000, "below_median_pct": 30},
        "scheduler": {"interval_hours": 1, "interval_minutes": None},
        "api": {"host": "127.0.0.1", "port": 9999},
    }
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(cfg), encoding="utf-8")
    return p


@pytest.fixture()
def tmp_regions(tmp_path: Path) -> Path:
    d = tmp_path / "regions"
    d.mkdir()
    region = {"id": "test_region", "label": "Test", "airports": ["LHR", "CDG", "FRA"]}
    (d / "test_region.yaml").write_text(yaml.dump(region), encoding="utf-8")
    return d


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def sample_quotes() -> List[QuoteSnapshot]:
    now = datetime.now(tz=timezone.utc)
    base = [
        QuoteSnapshot(
            search_ts=now, run_id="aaa", origin="BOS", destination="LHR",
            departure_date=date(2026, 6, 1), return_date=date(2026, 6, 8),
            trip_type="round_trip", currency="USD", total_price=Decimal("800"),
            source="stub",
        ),
        QuoteSnapshot(
            search_ts=now, run_id="aaa", origin="BOS", destination="CDG",
            departure_date=date(2026, 6, 5), return_date=date(2026, 6, 12),
            trip_type="round_trip", currency="USD", total_price=Decimal("600"),
            source="stub",
        ),
        QuoteSnapshot(
            search_ts=now, run_id="aaa", origin="BOS", destination="FRA",
            departure_date=date(2026, 6, 10), return_date=date(2026, 6, 17),
            trip_type="round_trip", currency="USD", total_price=Decimal("1200"),
            source="stub",
        ),
    ]
    return base
