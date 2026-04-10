from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
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


def plan_tasks(
    config: AppConfig,
    destination_airports: List[str],
) -> List[SearchTask]:
    """
    Generate (origin, dest, depart, return) tuples from config.
    Truncated by request_budget_per_run to prevent quota exhaustion.
    """
    departures = _sample_departure_dates(config)
    budget = config.collector.request_budget_per_run
    round_trip = config.trip.type == "round_trip"

    tasks: List[SearchTask] = []
    for origin in config.origin_airports:
        for dest in destination_airports:
            if origin == dest:
                continue
            for dep in departures:
                if round_trip:
                    for ret in _return_dates_for(dep, config):
                        tasks.append(SearchTask(origin, dest, dep, ret))
                else:
                    tasks.append(SearchTask(origin, dest, dep, None))
                if len(tasks) >= budget:
                    return tasks
    return tasks
