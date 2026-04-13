"""FastAPI application with local GUI and setup helpers."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from flight_deal_agent.settings import load_app_config
from flight_deal_agent.storage import (
    get_recent_deals,
    get_recent_quotes,
    get_run_log,
    init_db,
)

app = FastAPI(title="flight-deal-agent", version="0.2.1")
WEB_DIR = Path(__file__).parent / "web"
DEFAULT_SETUP_CONFIG: Dict[str, Any] = {
    "app": {"name": "flight-deal-agent", "timezone": "America/Vancouver"},
    "origin_airports": ["YVR"],
    "target_region_id": "us_ca_all_scheduled",
    "trip": {
        "type": "round_trip",
        "date_window": {
            "min_days_ahead": 7,
            "max_days_ahead": 60,
            "min_trip_nights": 2,
            "max_trip_nights": 10,
            "sample_every_n_days": 3,
            "trip_night_samples": [2, 3, 4, 5, 7],
        },
    },
    "currency": "USD",
    "collector": {"provider": "searchapi", "request_budget_per_run": 30},
    "amadeus": {"test_mode": True},
    "searchapi": {"gl": "us", "hl": "en"},
    "storage": {"sqlite_path": "data/state/quotes.db"},
    "alerts": {
        "channel": "stdout",
        "digest_interval_hours": 6,
        "cooldown_hours": 24,
        "renotify_price_drop_pct": 8,
    },
    "thresholds": {
        "max_total_price": None,
        "below_median_pct": None,
        "lowest_n_per_run": 5,
    },
    "scheduler": {"interval_hours": 1, "interval_minutes": None},
    "api": {"host": "127.0.0.1", "port": 8000},
}

_config_path: Optional[Path] = None
_regions_dir: Optional[Path] = None
_scheduler: Any = None  # set at startup


class StatusResponse(BaseModel):
    status: str
    scheduler_running: bool


class RunResponse(BaseModel):
    run_id: str
    task_count: int
    api_calls: int
    quote_count: int
    deal_count: int
    errors: List[str]


class SetupRequest(BaseModel):
    provider: Literal["searchapi", "amadeus", "stub"] = "searchapi"
    searchapi_api_key: str = ""
    amadeus_client_id: str = ""
    amadeus_client_secret: str = ""
    amadeus_test_mode: bool = True
    origin_airports: List[str] = Field(default_factory=lambda: ["YVR"])
    target_region_id: str = "us_ca_all_scheduled"
    timezone: str = "America/Vancouver"
    currency: str = "USD"
    gl: str = "us"
    hl: str = "en"
    request_budget_per_run: int = 30
    lowest_n_per_run: int = 5
    max_total_price: Optional[float] = None
    below_median_pct: Optional[float] = None
    interval_hours: int = 1
    interval_minutes: Optional[int] = None
    min_days_ahead: int = 7
    max_days_ahead: int = 60
    min_trip_nights: int = 2
    max_trip_nights: int = 10
    sample_every_n_days: int = 3
    trip_night_samples: List[int] = Field(default_factory=lambda: [2, 3, 4, 5, 7])


class SetupResponse(BaseModel):
    status: str
    config_path: str
    env_path: str
    scheduler_interval: str


def _project_root() -> Path:
    assert _config_path is not None
    if _config_path.parent.name == "config":
        return _config_path.parent.parent
    return _config_path.parent


def _env_path() -> Path:
    return _project_root() / ".env"


def _region_summaries() -> List[Dict[str, Any]]:
    if _regions_dir is None:
        return []
    items: List[Dict[str, Any]] = []
    for path in sorted(_regions_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        airports = data.get("airports") or []
        items.append(
            {
                "id": path.stem,
                "label": data.get("label", path.stem),
                "airport_count": len(airports),
            }
        )
    return items


def _write_env_values(path: Path, values: Dict[str, str]) -> None:
    current = {
        key: value
        for key, value in dotenv_values(path).items()
        if value is not None
    } if path.exists() else {}
    current.update(values)
    lines = [f"{key}={value}" for key, value in sorted(current.items()) if value != ""]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _build_config_payload(req: SetupRequest) -> Dict[str, Any]:
    data = deepcopy(DEFAULT_SETUP_CONFIG)
    data["app"]["timezone"] = req.timezone
    data["origin_airports"] = req.origin_airports
    data["target_region_id"] = req.target_region_id
    data["currency"] = req.currency
    data["collector"]["provider"] = req.provider
    data["collector"]["request_budget_per_run"] = req.request_budget_per_run
    data["searchapi"]["gl"] = req.gl
    data["searchapi"]["hl"] = req.hl
    data["amadeus"]["test_mode"] = req.amadeus_test_mode
    data["thresholds"]["lowest_n_per_run"] = req.lowest_n_per_run
    data["thresholds"]["max_total_price"] = req.max_total_price
    data["thresholds"]["below_median_pct"] = req.below_median_pct
    data["scheduler"]["interval_hours"] = req.interval_hours
    data["scheduler"]["interval_minutes"] = req.interval_minutes
    data["trip"]["date_window"]["min_days_ahead"] = req.min_days_ahead
    data["trip"]["date_window"]["max_days_ahead"] = req.max_days_ahead
    data["trip"]["date_window"]["min_trip_nights"] = req.min_trip_nights
    data["trip"]["date_window"]["max_trip_nights"] = req.max_trip_nights
    data["trip"]["date_window"]["sample_every_n_days"] = req.sample_every_n_days
    data["trip"]["date_window"]["trip_night_samples"] = req.trip_night_samples
    return data


def _apply_setup(req: SetupRequest) -> SetupResponse:
    if _config_path is None:
        raise HTTPException(500, "Not configured")
    config_data = _build_config_payload(req)
    _config_path.parent.mkdir(parents=True, exist_ok=True)
    _config_path.write_text(
        yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _write_env_values(
        _env_path(),
        {
            "SEARCHAPI_API_KEY": req.searchapi_api_key.strip(),
            "AMADEUS_CLIENT_ID": req.amadeus_client_id.strip(),
            "AMADEUS_CLIENT_SECRET": req.amadeus_client_secret.strip(),
        },
    )
    if _scheduler is not None:
        _scheduler.reconfigure(
            interval_hours=req.interval_hours,
            interval_minutes=req.interval_minutes,
        )
    cfg = load_app_config(_config_path)
    return SetupResponse(
        status="saved",
        config_path=str(_config_path),
        env_path=str(_env_path()),
        scheduler_interval=cfg.scheduler.label,
    )


def configure(config_path: Path, regions_dir: Path, scheduler: Any) -> None:
    global _config_path, _regions_dir, _scheduler
    _config_path = config_path
    _regions_dir = regions_dir
    _scheduler = scheduler


def _db_path() -> Path:
    assert _config_path is not None
    cfg = load_app_config(_config_path)
    return Path(cfg.storage.sqlite_path)


@app.get("/")
def gui_index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/app.css")
def gui_css() -> FileResponse:
    return FileResponse(WEB_DIR / "app.css", media_type="text/css")


@app.get("/app.js")
def gui_js() -> FileResponse:
    return FileResponse(WEB_DIR / "app.js", media_type="application/javascript")


@app.get("/api/health", response_model=StatusResponse)
def health() -> Dict[str, Any]:
    running = _scheduler.is_running if _scheduler else False
    return {"status": "ok", "scheduler_running": running}


@app.get("/api/deals")
def deals(limit: int = 50) -> List[Dict]:
    return get_recent_deals(_db_path(), limit)


@app.get("/api/quotes")
def quotes(limit: int = 100) -> List[Dict]:
    return get_recent_quotes(_db_path(), limit)


@app.get("/api/runs")
def runs(limit: int = 20) -> List[Dict]:
    return get_run_log(_db_path(), limit)


@app.post("/api/run", response_model=RunResponse)
def trigger_run() -> Dict[str, Any]:
    if _config_path is None or _regions_dir is None:
        raise HTTPException(500, "Server not configured")
    from flight_deal_agent.runner import run_once
    summary = run_once(_config_path, regions_dir=_regions_dir)
    return {
        "run_id": summary.run_id,
        "task_count": summary.task_count,
        "api_calls": summary.api_calls,
        "quote_count": summary.quote_count,
        "deal_count": summary.deal_count,
        "errors": summary.errors,
    }


@app.post("/api/scheduler/start")
def scheduler_start() -> Dict[str, str]:
    if _scheduler is None:
        raise HTTPException(500, "Scheduler not configured")
    _scheduler.start()
    return {"status": "started"}


@app.post("/api/scheduler/stop")
def scheduler_stop() -> Dict[str, str]:
    if _scheduler is None:
        raise HTTPException(500, "Scheduler not configured")
    _scheduler.stop()
    return {"status": "stopped"}


@app.get("/api/scheduler/status")
def scheduler_status() -> Dict[str, Any]:
    running = _scheduler.is_running if _scheduler else False
    return {"running": running}


@app.get("/api/config")
def get_config() -> Dict[str, Any]:
    if _config_path is None:
        raise HTTPException(500, "Not configured")
    cfg = load_app_config(_config_path)
    data = cfg.model_dump()
    if "amadeus" in data:
        data["amadeus"].pop("client_id", None)
        data["amadeus"].pop("client_secret", None)
    if "searchapi" in data:
        data["searchapi"].pop("api_key", None)
    return data


@app.get("/api/gui/bootstrap")
def gui_bootstrap() -> Dict[str, Any]:
    config = get_config()
    env_values = dotenv_values(_env_path()) if _env_path().exists() else {}
    return {
        "config": config,
        "regions": _region_summaries(),
        "provider_options": ["searchapi", "amadeus", "stub"],
        "secret_status": {
            "searchapi_api_key_set": bool(env_values.get("SEARCHAPI_API_KEY")),
            "amadeus_client_id_set": bool(env_values.get("AMADEUS_CLIENT_ID")),
            "amadeus_client_secret_set": bool(env_values.get("AMADEUS_CLIENT_SECRET")),
        },
        "paths": {
            "config": str(_config_path) if _config_path else "",
            "env": str(_env_path()),
        },
    }


@app.post("/api/setup", response_model=SetupResponse)
def save_setup(request: SetupRequest) -> SetupResponse:
    return _apply_setup(request)
