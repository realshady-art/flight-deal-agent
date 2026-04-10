from pathlib import Path

from flight_deal_agent.orchestrator import plan_tasks
from flight_deal_agent.settings import load_app_config


def test_plan_tasks_generates_tasks(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    destinations = ["LHR", "CDG", "FRA"]
    tasks = plan_tasks(cfg, destinations)
    assert len(tasks) > 0
    for t in tasks:
        assert t.origin == "BOS"
        assert t.destination in destinations
        assert t.departure_date is not None


def test_plan_tasks_respects_budget(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    destinations = ["LHR", "CDG", "FRA"]
    tasks = plan_tasks(cfg, destinations)
    assert len(tasks) <= cfg.collector.request_budget_per_run


def test_plan_tasks_skips_same_airport(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    tasks = plan_tasks(cfg, ["BOS", "LHR"])
    for t in tasks:
        assert t.origin != t.destination
