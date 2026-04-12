"""
Analyst: evaluate quotes against pricing rules and produce DealCandidates.

Rules applied (in order):
  1. Absolute price cap – quote.total_price <= thresholds.max_total_price
  2. Historical median drop – quote is at least below_median_pct% below
     the 30-day median for the same route.
  3. Notification cooldown – skip if same route was notified recently,
     unless price dropped further by renotify_price_drop_pct%.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from flight_deal_agent.models import DealCandidate, QuoteSnapshot
from flight_deal_agent.settings import AppConfig
from flight_deal_agent.storage import compute_median, get_route_history, was_recently_notified

logger = logging.getLogger(__name__)


def _check_absolute(config: AppConfig, quote: QuoteSnapshot) -> Optional[str]:
    cap = config.thresholds.max_total_price
    if cap is not None and float(quote.total_price) > cap:
        return None
    return "pass"


def _check_relative(
    config: AppConfig,
    quote: QuoteSnapshot,
    db_path: Path,
) -> tuple:
    """Returns (pass: bool, median: Decimal|None, drop_pct: float|None)."""
    pct_threshold = config.thresholds.below_median_pct
    if pct_threshold is None:
        return True, None, None

    history = get_route_history(db_path, quote.origin, quote.destination)
    if len(history) < 3:
        return True, None, None

    median = compute_median(history)
    if median is None or median == 0:
        return True, median, None

    drop = float((median - quote.total_price) / median * 100)
    if drop >= pct_threshold:
        return True, median, drop
    return False, median, drop


def _check_cooldown(
    config: AppConfig,
    quote: QuoteSnapshot,
    db_path: Path,
) -> bool:
    """Return True if we should notify (not cooled down, or price dropped enough)."""
    notified, last_price = was_recently_notified(
        db_path, quote.origin, quote.destination, config.alerts.cooldown_hours,
    )
    if not notified:
        return True
    if last_price is None:
        return True

    drop_needed = Decimal(config.alerts.renotify_price_drop_pct)
    actual_drop = (last_price - quote.total_price) / last_price * 100
    return actual_drop >= drop_needed


def _evaluate_lowest_n(
    config: AppConfig,
    quotes: List[QuoteSnapshot],
) -> List[DealCandidate]:
    limit = config.thresholds.lowest_n_per_run
    if not limit:
        return []

    ranked = sorted(
        quotes,
        key=lambda q: (
            q.total_price,
            q.departure_date,
            q.return_date or q.departure_date,
            q.origin,
            q.destination,
        ),
    )[:limit]

    deals = [
        DealCandidate(
            quote=q,
            reason=f"本轮最低价 Top {idx}/{len(ranked)}",
        )
        for idx, q in enumerate(ranked, start=1)
    ]
    logger.info("Analyst: %d quotes → %d cheapest candidates", len(quotes), len(deals))
    return deals


def evaluate_deals(
    config: AppConfig,
    quotes: List[QuoteSnapshot],
    db_path: Path,
) -> List[DealCandidate]:
    if config.thresholds.lowest_n_per_run:
        return _evaluate_lowest_n(config, quotes)

    deals: List[DealCandidate] = []
    for q in quotes:
        # 1. absolute cap
        if _check_absolute(config, q) is None:
            continue

        # 2. relative to history
        rel_pass, median, drop_pct = _check_relative(config, q, db_path)
        if not rel_pass:
            continue

        # 3. cooldown
        if not _check_cooldown(config, q, db_path):
            continue

        # build reason string
        parts = []
        if median is not None and drop_pct is not None:
            parts.append(f"低于历史中位价 {drop_pct:.1f}%（中位 {median}）")
        cap = config.thresholds.max_total_price
        if cap is not None:
            parts.append(f"低于上限 {cap}")
        reason = "；".join(parts) if parts else "符合筛选条件"

        deals.append(DealCandidate(
            quote=q,
            reason=reason,
            historical_median=median,
            drop_pct=drop_pct,
        ))

    logger.info("Analyst: %d quotes → %d deals", len(quotes), len(deals))
    return deals
