from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TripType = Literal["round_trip", "one_way"]


class QuoteSnapshot(BaseModel):
    """单次询价得到的结构化快照（字段随数据源扩展）。"""

    search_ts: datetime
    origin: str = Field(..., description="出发机场 IATA")
    destination: str = Field(..., description="到达机场 IATA")
    departure_date: date
    return_date: Optional[date] = None
    trip_type: TripType = "round_trip"
    currency: str
    total_price: Decimal
    source: str = Field(..., description="数据源标识，如 stub / amadeus")
    stops: Optional[int] = None
    carrier_codes: Optional[List[str]] = None
    deep_link: Optional[str] = None


class DealCandidate(BaseModel):
    """通过策略层筛选后的候选 deal，用于通知与汇总。"""

    quote: QuoteSnapshot
    reason: str = Field(..., description="人类可读或规则摘要")
