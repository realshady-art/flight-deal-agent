from __future__ import annotations

from flight_deal_agent.models import DealCandidate, QuoteSnapshot
from flight_deal_agent.settings import AppConfig


def evaluate_deals(config: AppConfig, quotes: list[QuoteSnapshot]) -> list[DealCandidate]:
    """
    策略层占位：当前不做历史对比与复杂规则，仅透传空列表。
    后续在此实现分位数、阈值、节假日上下文等。
    """
    _ = config
    _ = quotes
    return []
