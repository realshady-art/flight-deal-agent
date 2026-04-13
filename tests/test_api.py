from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flight_deal_agent.api import app, configure
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
    assert "flight-deal-agent control room" in resp.text


def test_gui_bootstrap(client: TestClient):
    resp = client.get("/api/gui/bootstrap")
    assert resp.status_code == 200
    body = resp.json()
    assert body["config"]["origin_airport"] == "YVR"
    assert body["paths"]["config"].endswith("local_web_search.yaml")
    assert "runner" in body["paths"]


def test_setup_writes_local_search_config(client: TestClient, tmp_config: Path):
    resp = client.post(
        "/api/setup",
        json={
            "origin_airport": "SEA",
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
    assert "origin_airport: SEA" in text
    assert "destination_scope: 美国西海岸" in text
