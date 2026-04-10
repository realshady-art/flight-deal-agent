from __future__ import annotations

from flight_deal_agent.models import DealCandidate
from flight_deal_agent.settings import AppConfig


def notify_deals(config: AppConfig, deals: list[DealCandidate]) -> None:
    """通知占位：stdout 渠道打印摘要。"""
    if config.alerts.channel != "stdout":
        raise NotImplementedError(f"通知渠道 {config.alerts.channel!r} 尚未实现")

    if not deals:
        print("[flight-deal-agent] 本轮无候选 deal。")
        return

    print(f"[flight-deal-agent] 本轮候选 deal数量: {len(deals)}")
    for d in deals:
        q = d.quote
        ret = q.return_date.isoformat() if q.return_date else "-"
        print(
            f"  - {q.origin}->{q.destination} 去程 {q.departure_date} 返程 {ret} "
            f"{q.total_price} {q.currency} | {d.reason}"
        )
