from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class DateWindow(BaseModel):
    min_days_ahead: int = 14
    max_days_ahead: int = 90
    min_trip_nights: int = 4
    max_trip_nights: int = 14
    sample_every_n_days: int = 7
    trip_night_samples: List[int] = Field(default_factory=lambda: [5, 7, 10])


class TripConfig(BaseModel):
    type: str = "round_trip"
    date_window: DateWindow = Field(default_factory=DateWindow)


class CollectorConfig(BaseModel):
    provider: str = "stub"
    request_budget_per_run: int = 30


class AmadeusConfig(BaseModel):
    test_mode: bool = True

    @property
    def client_id(self) -> str:
        return os.environ.get("AMADEUS_CLIENT_ID", "")

    @property
    def client_secret(self) -> str:
        return os.environ.get("AMADEUS_CLIENT_SECRET", "")

    @property
    def base_url(self) -> str:
        if self.test_mode:
            return "https://test.api.amadeus.com"
        return "https://api.amadeus.com"


class StorageConfig(BaseModel):
    sqlite_path: str = "data/state/quotes.db"


class AlertsConfig(BaseModel):
    channel: str = "stdout"
    digest_interval_hours: int = 6
    cooldown_hours: int = 24
    renotify_price_drop_pct: int = 8


class ThresholdsConfig(BaseModel):
    max_total_price: Optional[float] = None
    below_median_pct: Optional[float] = None


class SchedulerConfig(BaseModel):
    interval_hours: int = 1


class ApiConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


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
    amadeus: AmadeusConfig = Field(default_factory=AmadeusConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)


def load_app_config(path: Path) -> AppConfig:
    raw: Dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AppConfig.model_validate(raw)


def load_region_airports(regions_dir: Path, region_id: str) -> List[str]:
    region_file = regions_dir / f"{region_id}.yaml"
    if not region_file.is_file():
        raise FileNotFoundError(f"Region file not found: {region_file}")
    data = yaml.safe_load(region_file.read_text(encoding="utf-8"))
    airports = data.get("airports")
    if not isinstance(airports, list) or not all(isinstance(x, str) for x in airports):
        raise ValueError(f"Bad region file (need airports string list): {region_file}")
    return airports
