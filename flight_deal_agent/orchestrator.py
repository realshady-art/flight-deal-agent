from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from flight_deal_agent.settings import AppConfig


@dataclass(frozen=True)
class SearchTask:
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None


def _sample_departure_dates(config: AppConfig) -> List[date]:
    dw = config.trip.date_window
    today = date.today()
    start = today + timedelta(days=dw.min_days_ahead)
    end = today + timedelta(days=dw.max_days_ahead)
    dates: List[date] = []
    cur = start
    while cur <= end:
        dates.append(cur)
        cur += timedelta(days=dw.sample_every_n_days)
    return dates


def _return_dates_for(dep: date, config: AppConfig) -> List[date]:
    samples = config.trip.date_window.trip_night_samples
    mn = config.trip.date_window.min_trip_nights
    mx = config.trip.date_window.max_trip_nights
    return [dep + timedelta(days=n) for n in samples if mn <= n <= mx]


def _scheduler_interval_seconds(config: AppConfig) -> int:
    if config.scheduler.interval_minutes is not None:
        return config.scheduler.interval_minutes * 60
    return config.scheduler.interval_hours * 3600


def _apply_budget_window(
    tasks: List[SearchTask],
    config: AppConfig,
    *,
    now: Optional[datetime] = None,
) -> List[SearchTask]:
    budget = config.collector.request_budget_per_run
    if len(tasks) <= budget:
        return tasks

    chunk_count = math.ceil(len(tasks) / budget)
    current = now or datetime.now(tz=timezone.utc)
    slot = int(current.timestamp() // _scheduler_interval_seconds(config))
    start = (slot % chunk_count) * budget
    window = tasks[start:start + budget]
    if len(window) < budget:
        window.extend(tasks[:budget - len(window)])
    return window


def plan_tasks(
    config: AppConfig,
    origin_airports: List[str],
    destination_airports: List[str],
) -> List[SearchTask]:
    """
    Generate (origin, dest, depart, return) tuples from config.
    Truncated by request_budget_per_run to prevent quota exhaustion.
    """
    departures = _sample_departure_dates(config)
    round_trip = config.trip.type == "round_trip"

    tasks: List[SearchTask] = []
    for origin in origin_airports:
        for dest in destination_airports:
            if origin == dest:
                continue
            for dep in departures:
                if round_trip:
                    for ret in _return_dates_for(dep, config):
                        tasks.append(SearchTask(origin, dest, dep, ret))
                else:
                    tasks.append(SearchTask(origin, dest, dep, None))
    return _apply_budget_window(tasks, config)
