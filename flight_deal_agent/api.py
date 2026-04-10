"""FastAPI application — reserved for future frontend integration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from flight_deal_agent.settings import load_app_config
from flight_deal_agent.storage import (
    get_recent_deals,
    get_recent_quotes,
    get_run_log,
    init_db,
)

app = FastAPI(title="flight-deal-agent", version="0.2.0")

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


def configure(config_path: Path, regions_dir: Path, scheduler: Any) -> None:
    global _config_path, _regions_dir, _scheduler
    _config_path = config_path
    _regions_dir = regions_dir
    _scheduler = scheduler


def _db_path() -> Path:
    assert _config_path is not None
    cfg = load_app_config(_config_path)
    return Path(cfg.storage.sqlite_path)


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
    return data
