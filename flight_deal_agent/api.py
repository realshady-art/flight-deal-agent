"""FastAPI application with local GUI and setup helpers."""
from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from flight_deal_agent.local_search import (
    DEFAULT_LOCAL_SEARCH_CONFIG,
    LocalSearchRun,
    LocalWebSearchConfig,
    LocalWebSearchScheduler,
    load_local_search_config,
    read_recent_local_runs,
    run_local_web_search,
    save_local_search_config,
)
from flight_deal_agent.settings import load_app_config
from flight_deal_agent.storage import (
    get_recent_deals,
    get_recent_quotes,
    get_run_log,
    init_db,
)

app = FastAPI(title="flight-deal-agent", version="0.2.1")
WEB_DIR = Path(__file__).parent / "web"

_config_path: Optional[Path] = None
_regions_dir: Optional[Path] = None
_scheduler: Any = None  # set at startup
_local_search_scheduler: Optional[LocalWebSearchScheduler] = None


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


class SetupResponse(BaseModel):
    status: str
    config_path: str
    scheduler_interval: str
    log_path: str


def _dashboard_read_only() -> bool:
    return os.environ.get("FLIGHT_DEAL_DASHBOARD_READ_ONLY") == "1"


def _reject_if_read_only() -> None:
    if _dashboard_read_only():
        raise HTTPException(403, "Dashboard is running in read-only mode")


def _project_root() -> Path:
    assert _config_path is not None
    if _config_path.parent.name == "config":
        return _config_path.parent.parent
    return _config_path.parent


def _local_search_config_path() -> Path:
    return _project_root() / "config" / "local_web_search.yaml"


def _local_search_log_path() -> Path:
    return _project_root() / "data" / "state" / "local_web_search_runs.jsonl"


def _local_search_template_path() -> Path:
    return _project_root() / "scripts" / "hourly_flight_web_search_terminal_prompt.txt"


def _apply_setup(req: LocalWebSearchConfig) -> SetupResponse:
    save_local_search_config(_local_search_config_path(), req)
    if _local_search_scheduler is not None:
        _local_search_scheduler.reconfigure()
    return SetupResponse(
        status="saved",
        config_path=str(_local_search_config_path()),
        scheduler_interval=f"{req.interval_hours}h",
        log_path=str(_local_search_log_path()),
    )


def configure(config_path: Path, regions_dir: Path, scheduler: Any) -> None:
    global _config_path, _regions_dir, _scheduler, _local_search_scheduler
    _config_path = config_path
    _regions_dir = regions_dir
    _scheduler = scheduler
    _local_search_scheduler = LocalWebSearchScheduler(
        workdir=_project_root(),
        config_path=_local_search_config_path(),
        template_path=_local_search_template_path(),
        log_path=_local_search_log_path(),
    )


def ensure_local_search_runtime_started() -> None:
    if _local_search_scheduler is None:
        return
    _local_search_scheduler.start()
    _local_search_scheduler.ensure_fresh_results()


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
    _reject_if_read_only()
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
    _reject_if_read_only()
    if _scheduler is None:
        raise HTTPException(500, "Scheduler not configured")
    _scheduler.start()
    return {"status": "started"}


@app.post("/api/scheduler/stop")
def scheduler_stop() -> Dict[str, str]:
    _reject_if_read_only()
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
    cfg = load_local_search_config(_local_search_config_path())
    codex_ok = True
    codex_error = None
    try:
        from flight_deal_agent.local_search import resolve_codex_bin
        codex_path = resolve_codex_bin()
    except Exception as exc:  # noqa: BLE001
        codex_ok = False
        codex_path = None
        codex_error = str(exc)
    return {
        "config": cfg.model_dump(),
        "defaults": DEFAULT_LOCAL_SEARCH_CONFIG,
        "codex": {
            "available": codex_ok,
            "path": codex_path,
            "error": codex_error,
            "host": socket.gethostname(),
        },
        "paths": {
            "config": str(_local_search_config_path()),
            "log": str(_local_search_log_path()),
            "prompt_template": str(_local_search_template_path()),
            "runner": str(_project_root() / "scripts" / "hourly_flight_web_search_terminal.py"),
        },
        "recent_runs": read_recent_local_runs(_local_search_log_path(), limit=6),
        "read_only_dashboard": _dashboard_read_only(),
    }


@app.post("/api/setup", response_model=SetupResponse)
def save_setup(request: LocalWebSearchConfig) -> SetupResponse:
    _reject_if_read_only()
    return _apply_setup(request)


@app.post("/api/local/run")
def run_local_agent() -> Dict[str, Any]:
    _reject_if_read_only()
    try:
        if _local_search_scheduler is not None:
            run = _local_search_scheduler.run_now()
        else:
            run = run_local_web_search(
                workdir=_project_root(),
                config_path=_local_search_config_path(),
                template_path=_local_search_template_path(),
                log_path=_local_search_log_path(),
            )
        return run.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        recent = read_recent_local_runs(_local_search_log_path(), limit=1)
        payload = recent[0] if recent else {}
        return {
            "status": "error",
            "error": str(exc),
            "last_run": payload,
        }


@app.post("/api/local/search-now")
def run_local_agent_from_dashboard() -> Dict[str, Any]:
    try:
        if _local_search_scheduler is not None:
            run = _local_search_scheduler.run_now()
        else:
            run = run_local_web_search(
                workdir=_project_root(),
                config_path=_local_search_config_path(),
                template_path=_local_search_template_path(),
                log_path=_local_search_log_path(),
            )
        return run.model_dump(mode="json")
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        recent = read_recent_local_runs(_local_search_log_path(), limit=1)
        payload = recent[0] if recent else {}
        return {
            "status": "error",
            "error": str(exc),
            "last_run": payload,
        }


@app.get("/api/local/runs")
def recent_local_runs(limit: int = 10) -> List[Dict[str, Any]]:
    return read_recent_local_runs(_local_search_log_path(), limit=limit)


@app.post("/api/local/scheduler/start")
def local_scheduler_start() -> Dict[str, Any]:
    _reject_if_read_only()
    if _local_search_scheduler is None:
        raise HTTPException(500, "Local scheduler not configured")
    _local_search_scheduler.start()
    return {"status": "started"}


@app.post("/api/local/scheduler/stop")
def local_scheduler_stop() -> Dict[str, Any]:
    _reject_if_read_only()
    if _local_search_scheduler is None:
        raise HTTPException(500, "Local scheduler not configured")
    _local_search_scheduler.stop()
    return {"status": "stopped"}


@app.get("/api/local/scheduler/status")
def local_scheduler_status() -> Dict[str, Any]:
    running = _local_search_scheduler.is_running if _local_search_scheduler else False
    return {"running": running}
