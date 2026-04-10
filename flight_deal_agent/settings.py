from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import yaml
from pydantic import BaseModel, Field


class DateWindow(BaseModel):
    min_days_ahead: int = 14
    max_days_ahead: int = 90
    min_trip_nights: int = 4
    max_trip_nights: int = 14


class TripConfig(BaseModel):
    type: str = "round_trip"
    date_window: DateWindow = Field(default_factory=DateWindow)


class CollectorConfig(BaseModel):
    provider: str = "stub"
    request_budget_per_run: int = 50


class StorageConfig(BaseModel):
    sqlite_path: str = "data/state/quotes.db"


class AlertsConfig(BaseModel):
    channel: str = "stdout"
    digest_interval_hours: int = 6
    cooldown_hours: int = 24
    renotify_price_drop_pct: int = 8


class ThresholdsConfig(BaseModel):
    max_total_price: Optional[float] = None
    below_historical_median_pct: Optional[float] = None


class AppMeta(BaseModel):
    name: str = "flight-deal-agent"
    timezone: str = "Asia/Shanghai"


class AppConfig(BaseModel):
    app: AppMeta = Field(default_factory=AppMeta)
    origin_airports: List[str]
    target_region_id: str
    trip: TripConfig = Field(default_factory=TripConfig)
    currency: str = "CNY"
    collector: CollectorConfig = Field(default_factory=CollectorConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)


def load_app_config(path: Path) -> AppConfig:
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AppConfig.model_validate(raw)


def load_region_airports(regions_dir: Path, region_id: str) -> List[str]:
    region_file = regions_dir / f"{region_id}.yaml"
    if not region_file.is_file():
        raise FileNotFoundError(f"区域文件不存在: {region_file}")
    data = yaml.safe_load(region_file.read_text(encoding="utf-8"))
    airports = data.get("airports")
    if not isinstance(airports, list) or not all(isinstance(x, str) for x in airports):
        raise ValueError(f"区域文件格式错误（需要 airports 字符串列表）: {region_file}")
    return airports
