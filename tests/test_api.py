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
