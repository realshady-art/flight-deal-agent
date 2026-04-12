from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, model_validator


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


class SearchApiConfig(BaseModel):
    base_url: str = "https://www.searchapi.io"
    gl: str = "us"
    hl: str = "en"

    @property
    def api_key(self) -> str:
        return os.environ.get("SEARCHAPI_API_KEY", "")


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
    lowest_n_per_run: Optional[int] = Field(default=None, gt=0)


class SchedulerConfig(BaseModel):
    interval_hours: int = Field(default=1, gt=0)
    interval_minutes: Optional[int] = Field(default=None, gt=0)

    @property
    def label(self) -> str:
        if self.interval_minutes is not None:
            return f"{self.interval_minutes}m"
        return f"{self.interval_hours}h"


class ApiConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


class AppMeta(BaseModel):
    name: str = "flight-deal-agent"
    timezone: str = "Asia/Shanghai"


class AppConfig(BaseModel):
    app: AppMeta = Field(default_factory=AppMeta)
    origin_airports: List[str] = Field(default_factory=list)
    origin_region_id: Optional[str] = None
    target_region_id: str
    trip: TripConfig = Field(default_factory=TripConfig)
    currency: str = "CNY"
    collector: CollectorConfig = Field(default_factory=CollectorConfig)
    amadeus: AmadeusConfig = Field(default_factory=AmadeusConfig)
    searchapi: SearchApiConfig = Field(default_factory=SearchApiConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    thresholds: ThresholdsConfig = Field(default_factory=ThresholdsConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)

    @model_validator(mode="after")
    def validate_origins(self) -> "AppConfig":
        if not self.origin_airports and not self.origin_region_id:
            raise ValueError("Need either origin_airports or origin_region_id")
        return self


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
