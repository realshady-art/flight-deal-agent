from datetime import datetime, timezone
from pathlib import Path

from flight_deal_agent.orchestrator import SearchTask, _apply_budget_window, plan_tasks
from flight_deal_agent.settings import load_app_config


def test_plan_tasks_generates_tasks(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    origins = ["BOS"]
    destinations = ["LHR", "CDG", "FRA"]
    tasks = plan_tasks(cfg, origins, destinations)
    assert len(tasks) > 0
    for t in tasks:
        assert t.origin == "BOS"
        assert t.destination in destinations
        assert t.departure_date is not None


def test_plan_tasks_respects_budget(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    origins = ["BOS"]
    destinations = ["LHR", "CDG", "FRA"]
    tasks = plan_tasks(cfg, origins, destinations)
    assert len(tasks) <= cfg.collector.request_budget_per_run


def test_plan_tasks_skips_same_airport(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    tasks = plan_tasks(cfg, ["BOS"], ["BOS", "LHR"])
    for t in tasks:
        assert t.origin != t.destination


def test_budget_window_rotates_between_intervals(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    cfg.collector.request_budget_per_run = 2
    cfg.scheduler.interval_minutes = 10
    cfg.scheduler.interval_hours = 1

    tasks = [
        SearchTask("BOS", "LHR", datetime(2026, 6, 1, tzinfo=timezone.utc).date()),
        SearchTask("BOS", "CDG", datetime(2026, 6, 2, tzinfo=timezone.utc).date()),
        SearchTask("BOS", "FRA", datetime(2026, 6, 3, tzinfo=timezone.utc).date()),
        SearchTask("BOS", "MAD", datetime(2026, 6, 4, tzinfo=timezone.utc).date()),
    ]

    rotated_a = _apply_budget_window(
        list(tasks),
        cfg,
        now=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
    )
    rotated_b = _apply_budget_window(
        list(tasks),
        cfg,
        now=datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc),
    )
    assert rotated_a != rotated_b
