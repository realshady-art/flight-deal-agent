from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TripType = Literal["round_trip", "one_way"]


class QuoteSnapshot(BaseModel):
    search_ts: datetime
    run_id: str = ""
    origin: str = Field(..., description="IATA")
    destination: str = Field(..., description="IATA")
    departure_date: date
    return_date: Optional[date] = None
    trip_type: TripType = "round_trip"
    currency: str
    total_price: Decimal
    source: str = Field(..., description="stub / amadeus-inspiration / amadeus-offers")
    stops: Optional[int] = None
    carrier_codes: Optional[List[str]] = None
    deep_link: Optional[str] = None


class DealCandidate(BaseModel):
    quote: QuoteSnapshot
    reason: str
    historical_median: Optional[Decimal] = None
    drop_pct: Optional[float] = None


class RunSummary(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    task_count: int
    api_calls: int
    quote_count: int
    deal_count: int
    errors: List[str] = Field(default_factory=list)
