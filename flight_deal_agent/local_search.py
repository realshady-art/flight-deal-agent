from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel, Field


DEFAULT_LOCAL_SEARCH_CONFIG: Dict[str, Any] = {
    "origin_airports": ["YVR", "YXX"],
    "destination_scope": "美国/加拿大",
    "top_n": 10,
    "interval_hours": 1,
    "notes": "只用 web search，不用付费 API，不用浏览器自动化。",
    "model": "gpt-5.4",
    "reasoning_effort": "medium",
}

JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


class LocalWebSearchConfig(BaseModel):
    origin_airports: List[str] = Field(default_factory=lambda: ["YVR", "YXX"])
    destination_scope: str = "美国/加拿大"
    top_n: int = Field(default=10, gt=0)
    interval_hours: int = Field(default=1, gt=0)
    notes: str = "只用 web search，不用付费 API，不用浏览器自动化。"
    model: str = "gpt-5.4"
    reasoning_effort: str = "medium"


class LocalSearchFinding(BaseModel):
    route: str
    origin_airport: str
    destination_airport: str
    price_display: str
    price_value: Optional[float] = None
    currency: Optional[str] = None
    date_range: str
    source_name: str
    source_url: str
    note: str = ""


class LocalSearchRun(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    status: str
    output: str = ""
    error: Optional[str] = None
    headline: Optional[str] = None
    findings: List[LocalSearchFinding] = Field(default_factory=list)
    narrative_summary: Optional[str] = None

    @property
    def preview(self) -> str:
        text = self.output.strip() or (self.error or "")
        text = " ".join(text.split())
        return text[:180]


def load_local_search_config(path: Path) -> LocalWebSearchConfig:
    if not path.exists():
        return LocalWebSearchConfig.model_validate(DEFAULT_LOCAL_SEARCH_CONFIG)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "origin_airports" not in raw and raw.get("origin_airport"):
        raw["origin_airports"] = [raw["origin_airport"]]
    raw.pop("origin_airport", None)
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
        origin_airports=", ".join(config.origin_airports),
        destination_scope=config.destination_scope,
        top_n=config.top_n,
        notes=config.notes.strip(),
    )


def resolve_codex_bin() -> str:
    codex_bin = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not codex_bin:
        raise RuntimeError("Could not find `codex` in PATH. Set CODEX_BIN explicitly.")
    return codex_bin


def _extract_json_payload(output: str) -> Dict[str, Any]:
    match = JSON_BLOCK_RE.search(output)
    if not match:
        return {}
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _extract_narrative_text(output: str) -> str:
    text = JSON_BLOCK_RE.sub("", output).strip()
    return text


def _parse_findings(payload: Dict[str, Any]) -> List[LocalSearchFinding]:
    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, list):
        return []
    findings: List[LocalSearchFinding] = []
    for raw in raw_findings:
        if not isinstance(raw, dict):
            continue
        try:
            findings.append(LocalSearchFinding.model_validate(raw))
        except Exception:
            continue
    return findings


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
    payload = _extract_json_payload(output)
    findings = _parse_findings(payload)
    headline = payload.get("headline") if isinstance(payload.get("headline"), str) else None
    narrative_summary = (
        payload.get("summary")
        if isinstance(payload.get("summary"), str)
        else _extract_narrative_text(output) or None
    )
    run = LocalSearchRun(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        output=output,
        error=error,
        headline=headline,
        findings=findings,
        narrative_summary=narrative_summary,
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
        self._job_lock = threading.Lock()

    def _run_job(self) -> None:
        if not self._job_lock.acquire(blocking=False):
            return
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
        finally:
            self._job_lock.release()

    def run_now(self) -> LocalSearchRun:
        if not self._job_lock.acquire(blocking=False):
            raise RuntimeError("Local search is already running")
        try:
            return run_local_web_search(
                workdir=self._workdir,
                config_path=self._config_path,
                template_path=self._template_path,
                log_path=self._log_path,
            )
        finally:
            self._job_lock.release()

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

    def ensure_fresh_results(self) -> None:
        cfg = load_local_search_config(self._config_path)
        recent = read_recent_local_runs(self._log_path, limit=1)
        if recent:
            latest = recent[0]
            finished_at = latest.get("finished_at")
            if finished_at:
                try:
                    ts = datetime.fromisoformat(finished_at)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    age_seconds = (datetime.now(tz=timezone.utc) - ts).total_seconds()
                    if age_seconds < cfg.interval_hours * 3600:
                        return
                except ValueError:
                    pass
        threading.Thread(target=self._run_job, daemon=True).start()

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
