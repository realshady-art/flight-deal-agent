from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from flight_deal_agent.models import QuoteSnapshot
from flight_deal_agent.orchestrator import SearchTask
from flight_deal_agent.settings import AppConfig


def collect_quotes_stub(
    config: AppConfig,
    tasks: list[SearchTask],
) -> list[QuoteSnapshot]:
    """
    占位采集器：不调用任何外部 API，返回空列表。
    接入真实 provider 时在此处分支或拆分为独立模块。
    """
    _ = (config, tasks)
    return []


def collect_quotes(
    config: AppConfig,
    tasks: list[SearchTask],
) -> list[QuoteSnapshot]:
    provider = config.collector.provider
    if provider == "stub":
        return collect_quotes_stub(config, tasks)
    raise NotImplementedError(
        f"collector.provider={provider!r} 尚未实现；请使用 stub 或扩展 collector 模块。"
    )


def make_demo_quote(task: SearchTask, currency: str) -> QuoteSnapshot:
    """仅用于本地演示通知链路；run-once 默认不使用。"""
    return QuoteSnapshot(
        search_ts=datetime.now(tz=timezone.utc),
        origin=task.origin,
        destination=task.destination,
        departure_date=datetime.now(tz=timezone.utc).date(),
        return_date=None,
        trip_type="one_way",
        currency=currency,
        total_price=Decimal("999.00"),
        source="demo",
    )
