from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field


DEFAULT_LOCAL_SEARCH_CONFIG: Dict[str, Any] = {
    "origin_airport": "YVR",
    "destination_scope": "美国/加拿大",
    "top_n": 5,
    "interval_hours": 1,
    "notes": "只用 web search，不用付费 API，不用浏览器自动化。",
    "model": "gpt-5.4",
    "reasoning_effort": "medium",
}


class LocalWebSearchConfig(BaseModel):
    origin_airport: str = "YVR"
    destination_scope: str = "美国/加拿大"
    top_n: int = Field(default=5, gt=0)
    interval_hours: int = Field(default=1, gt=0)
    notes: str = "只用 web search，不用付费 API，不用浏览器自动化。"
    model: str = "gpt-5.4"
    reasoning_effort: str = "medium"


class LocalSearchRun(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    status: str
    output: str = ""
    error: Optional[str] = None

    @property
    def summary(self) -> str:
        text = self.output.strip() or (self.error or "")
        text = " ".join(text.split())
        return text[:180]


def load_local_search_config(path: Path) -> LocalWebSearchConfig:
    if not path.exists():
        return LocalWebSearchConfig.model_validate(DEFAULT_LOCAL_SEARCH_CONFIG)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return LocalWebSearchConfig.model_validate(raw)


def save_local_search_config(path: Path, config: LocalWebSearchConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(config.model_dump(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def render_local_search_prompt(template_path: Path, config: LocalWebSearchConfig) -> str:
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        origin_airport=config.origin_airport,
        destination_scope=config.destination_scope,
        top_n=config.top_n,
        notes=config.notes.strip(),
    )


def resolve_codex_bin() -> str:
    codex_bin = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not codex_bin:
        raise RuntimeError("Could not find `codex` in PATH. Set CODEX_BIN explicitly.")
    return codex_bin


def append_local_run(log_path: Path, run: LocalSearchRun) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(run.model_dump(mode="json"), ensure_ascii=False) + "\n")


def read_recent_local_runs(log_path: Path, limit: int = 10) -> List[Dict[str, Any]]:
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    items: List[Dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        raw = json.loads(line)
        items.append(raw)
    return items


def run_local_web_search(
    *,
    workdir: Path,
    config_path: Path,
    template_path: Path,
    log_path: Optional[Path] = None,
) -> LocalSearchRun:
    started_at = datetime.now(tz=timezone.utc)
    run_id = uuid4().hex[:12]
    cfg = load_local_search_config(config_path)
    prompt = render_local_search_prompt(template_path, cfg)
    cmd = [
        resolve_codex_bin(),
        "exec",
        "-C",
        str(workdir),
        "-m",
        cfg.model,
        "-s",
        "workspace-write",
        "--dangerously-bypass-approvals-and-sandbox",
        "-c",
        f'model_reasoning_effort="{cfg.reasoning_effort}"',
        prompt,
    ]
    result = subprocess.run(
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
    )
    finished_at = datetime.now(tz=timezone.utc)
    status = "ok" if result.returncode == 0 else "error"
    output = result.stdout.strip()
    error = result.stderr.strip() or None
    run = LocalSearchRun(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        output=output,
        error=error,
    )
    if log_path is not None:
        append_local_run(log_path, run)
    if result.returncode != 0:
        raise RuntimeError(error or output or "codex exec failed")
    return run


class LocalWebSearchScheduler:
    def __init__(self, *, workdir: Path, config_path: Path, template_path: Path, log_path: Path):
        self._workdir = workdir
        self._config_path = config_path
        self._template_path = template_path
        self._log_path = log_path
        self._scheduler: Optional[BackgroundScheduler] = None

    def _run_job(self) -> None:
        try:
            run_local_web_search(
                workdir=self._workdir,
                config_path=self._config_path,
                template_path=self._template_path,
                log_path=self._log_path,
            )
        except Exception as exc:  # noqa: BLE001
            run = LocalSearchRun(
                run_id=uuid4().hex[:12],
                started_at=datetime.now(tz=timezone.utc),
                finished_at=datetime.now(tz=timezone.utc),
                status="error",
                output="",
                error=str(exc),
            )
            append_local_run(self._log_path, run)

    def start(self) -> None:
        if self._scheduler and self._scheduler.running:
            return
        cfg = load_local_search_config(self._config_path)
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._run_job,
            trigger=IntervalTrigger(hours=cfg.interval_hours),
            id="local_web_search",
            replace_existing=True,
        )
        self._scheduler.start()

    def stop(self) -> None:
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def reconfigure(self) -> None:
        was_running = self.is_running
        if was_running:
            self.stop()
        if was_running:
            self.start()

    @property
    def is_running(self) -> bool:
        return bool(self._scheduler and self._scheduler.running)

    def recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return read_recent_local_runs(self._log_path, limit=limit)
