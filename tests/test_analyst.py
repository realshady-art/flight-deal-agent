from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import List

from flight_deal_agent.analyst import evaluate_deals
from flight_deal_agent.models import QuoteSnapshot
from flight_deal_agent.settings import load_app_config
from flight_deal_agent.storage import init_db, persist_quotes


def _make_quote(price: str, origin: str = "BOS", dest: str = "LHR") -> QuoteSnapshot:
    from datetime import date
    return QuoteSnapshot(
        search_ts=datetime.now(tz=timezone.utc),
        run_id="t",
        origin=origin,
        destination=dest,
        departure_date=date(2026, 7, 1),
        return_date=date(2026, 7, 8),
        trip_type="round_trip",
        currency="USD",
        total_price=Decimal(price),
        source="stub",
    )


def test_absolute_cap_filters(tmp_config: Path, tmp_db: Path):
    cfg = load_app_config(tmp_config)
    init_db(tmp_db)
    expensive = _make_quote("9999")
    deals = evaluate_deals(cfg, [expensive], tmp_db)
    assert len(deals) == 0


def test_cheap_passes_absolute(tmp_config: Path, tmp_db: Path):
    cfg = load_app_config(tmp_config)
    init_db(tmp_db)
    cheap = _make_quote("200")
    deals = evaluate_deals(cfg, [cheap], tmp_db)
    assert len(deals) == 1


def test_relative_threshold_with_history(tmp_config: Path, tmp_db: Path):
    """When history exists, only significantly cheaper quotes pass."""
    cfg = load_app_config(tmp_config)
    init_db(tmp_db)

    history = [_make_quote(str(p)) for p in [1000, 1100, 1050, 1020, 980]]
    persist_quotes(tmp_db, history)

    much_cheaper = _make_quote("500")
    deals = evaluate_deals(cfg, [much_cheaper], tmp_db)
    assert len(deals) == 1
    assert deals[0].drop_pct is not None
    assert deals[0].drop_pct > 30


def test_not_cheap_enough_relative(tmp_config: Path, tmp_db: Path):
    """Price only slightly below median should NOT produce a deal."""
    cfg = load_app_config(tmp_config)
    init_db(tmp_db)

    history = [_make_quote(str(p)) for p in [1000, 1100, 1050, 1020, 980]]
    persist_quotes(tmp_db, history)

    slightly_cheaper = _make_quote("900")
    deals = evaluate_deals(cfg, [slightly_cheaper], tmp_db)
    assert len(deals) == 0
