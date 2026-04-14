from datetime import datetime, timezone
from pathlib import Path
import time

import pytest
from fastapi.testclient import TestClient

from flight_deal_agent.api import app, configure
from flight_deal_agent.local_search import LocalSearchFinding, LocalSearchRun
from flight_deal_agent.scheduler import FlightDealScheduler
from flight_deal_agent.settings import load_app_config
from flight_deal_agent.storage import init_db


@pytest.fixture()
def client(tmp_config: Path, tmp_regions: Path) -> TestClient:
    cfg = load_app_config(tmp_config)
    db = Path(cfg.storage.sqlite_path)
    init_db(db)
    sched = FlightDealScheduler(tmp_config, tmp_regions)
    configure(tmp_config, tmp_regions, sched)
    return TestClient(app)


def test_health(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_deals_empty(client: TestClient):
    resp = client.get("/api/deals")
    assert resp.status_code == 200
    assert resp.json() == []


def test_quotes_empty(client: TestClient):
    resp = client.get("/api/quotes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_runs_empty(client: TestClient):
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_trigger_run(client: TestClient):
    resp = client.post("/api/run")
    assert resp.status_code == 200
    body = resp.json()
    assert "run_id" in body
    assert body["quote_count"] == 0


def test_config_endpoint(client: TestClient):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["origin_airports"] == ["BOS"]


def test_scheduler_status(client: TestClient):
    resp = client.get("/api/scheduler/status")
    assert resp.status_code == 200
    assert resp.json()["running"] is False


def test_root_serves_gui(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    assert "LOWFARE" in resp.text or "机票" in resp.text


def test_gui_bootstrap(client: TestClient):
    resp = client.get("/api/gui/bootstrap")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    body = resp.json()
    assert body["config"]["origin_airports"] == ["YVR", "YXX"]
    assert body["config"]["top_n"] == 10
    assert body["paths"]["config"].endswith("local_web_search.yaml")
    assert "host" in body["codex"]
    assert "runner" in body["paths"]


def test_static_assets_are_not_cached(client: TestClient):
    css = client.get("/app.css")
    js = client.get("/app.js")
    scheduler = client.get("/api/local/scheduler/status")
    assert css.status_code == 200
    assert js.status_code == 200
    assert scheduler.status_code == 200
    assert css.headers["cache-control"] == "no-store"
    assert js.headers["cache-control"] == "no-store"
    assert scheduler.headers["cache-control"] == "no-store"


def test_setup_writes_local_search_config(client: TestClient, tmp_config: Path):
    resp = client.post(
        "/api/setup",
        json={
            "origin_airports": ["SEA", "YXX"],
            "destination_scope": "美国西海岸",
            "top_n": 3,
            "interval_hours": 2,
            "notes": "优先看周末短途。",
            "model": "gpt-5.4",
            "reasoning_effort": "medium",
        },
    )
    assert resp.status_code == 200
    config_path = tmp_config.parent / "config" / "local_web_search.yaml"
    assert config_path.exists()
    text = config_path.read_text(encoding="utf-8")
    assert "- SEA" in text
    assert "top_n: 10" in text
    assert "destination_scope: 美国西海岸" in text


def test_read_only_dashboard_blocks_mutations(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("FLIGHT_DEAL_DASHBOARD_READ_ONLY", "1")
    for path in (
        "/api/setup",
        "/api/run",
        "/api/scheduler/start",
        "/api/scheduler/stop",
        "/api/local/run",
        "/api/local/scheduler/start",
        "/api/local/scheduler/stop",
    ):
        if path == "/api/setup":
            resp = client.post(
                path,
                json={
                    "origin_airports": ["SEA", "YXX"],
                    "destination_scope": "美国西海岸",
                    "top_n": 3,
                    "interval_hours": 2,
                    "notes": "优先看周末短途。",
                    "model": "gpt-5.4",
                    "reasoning_effort": "medium",
                },
            )
        else:
            resp = client.post(path)
        assert resp.status_code == 403


def test_read_only_dashboard_allows_manual_local_search(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("FLIGHT_DEAL_DASHBOARD_READ_ONLY", "1")

    def fake_run_now() -> LocalSearchRun:
        raise AssertionError("dashboard search-now should not reuse the scheduler lock")

    completed = {"value": False}

    def fake_direct_run(*args, **kwargs) -> LocalSearchRun:
        completed["value"] = True
        return LocalSearchRun(
            run_id="testrun123",
            started_at=datetime.now(tz=timezone.utc),
            finished_at=datetime.now(tz=timezone.utc),
            status="ok",
            headline="Manual server-side search finished",
            findings=[
                LocalSearchFinding(
                    route="YVR -> YYC",
                    origin_airport="YVR",
                    destination_airport="YYC",
                    price_display="CA$81 round trip",
                    price_value=81,
                    currency="CAD",
                    date_range="Apr 23-28",
                    source_name="Google Flights",
                    source_url="https://example.com/yyc",
                    note="Short-haul fare still stands out.",
                )
            ],
            narrative_summary="YYC is still the cheapest visible fare.",
        )

    monkeypatch.setattr("flight_deal_agent.api._local_search_scheduler.run_now", fake_run_now)
    monkeypatch.setattr("flight_deal_agent.api.run_local_web_search", fake_direct_run)
    resp = client.post("/api/local/search-now")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "accepted"
    for _ in range(50):
        if completed["value"]:
            break
        time.sleep(0.01)
    assert completed["value"] is True
    status = client.get("/api/local/search-status")
    assert status.status_code == 200
    status_body = status.json()
    assert status_body["manual_search"]["last_started_at"] is not None


def test_local_search_status_reports_scheduler_details(client: TestClient):
    resp = client.get("/api/local/search-status")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-store"
    body = resp.json()
    assert "manual_search" in body
    assert "scheduler" in body
    assert "running" in body["scheduler"]
    assert "job_running" in body["scheduler"]
    assert "next_run_at" in body["scheduler"]
