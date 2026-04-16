"""
Notifier: deliver deal alerts to the user.

Channels:
  - stdout  : print to terminal (implemented)
  - telegram: (reserved interface, not yet implemented)
  - email   : (reserved interface, not yet implemented)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from flight_deal_agent.models import DealCandidate
from flight_deal_agent.settings import AppConfig
from flight_deal_agent.storage import record_notification

logger = logging.getLogger(__name__)


def _format_deal(d: DealCandidate) -> str:
    q = d.quote
    ret = q.return_date.isoformat() if q.return_date else "-"
    carriers = ",".join(q.carrier_codes) if q.carrier_codes else "?"
    stops_str = f"{q.stops}stop" if q.stops is not None else ""
    return (
        f"  {q.origin} → {q.destination}  "
        f"去 {q.departure_date}  返 {ret}  "
        f"{q.total_price} {q.currency}  "
        f"[{carriers} {stops_str}]  "
        f"| {d.reason}"
    )


def _notify_stdout(deals: List[DealCandidate]) -> None:
    if not deals:
        print("[OrbitScan] 本轮无结果。")
        return
    if all(d.reason.startswith("本轮最低价 Top ") for d in deals):
        print(f"[OrbitScan] 当前最低的 {len(deals)} 条报价：")
    else:
        print(f"[OrbitScan] 发现 {len(deals)} 条候选 deal：")
    for d in deals:
        print(_format_deal(d))


def _notify_telegram(deals: List[DealCandidate]) -> None:
    raise NotImplementedError("Telegram notifier 尚未实现")


def _notify_email(deals: List[DealCandidate]) -> None:
    raise NotImplementedError("Email notifier 尚未实现")


def notify_deals(
    config: AppConfig,
    deals: List[DealCandidate],
    db_path: Path,
) -> None:
    """Send notifications and record to DB for cooldown tracking."""
    channel = config.alerts.channel
    if channel == "stdout":
        _notify_stdout(deals)
    elif channel == "telegram":
        _notify_telegram(deals)
    elif channel == "email":
        _notify_email(deals)
    else:
        raise ValueError(f"Unknown alert channel: {channel!r}")

    for d in deals:
        try:
            record_notification(db_path, d)
        except Exception:
            logger.warning("Failed to record notification", exc_info=True)
