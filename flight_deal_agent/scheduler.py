"""Periodic scheduler wrapping APScheduler."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from flight_deal_agent.runner import run_once

logger = logging.getLogger(__name__)

JOB_ID = "flight_scan"


class FlightDealScheduler:
    def __init__(
        self,
        config_path: Path,
        regions_dir: Path,
        interval_hours: int = 1,
    ):
        self._config_path = config_path
        self._regions_dir = regions_dir
        self._interval = interval_hours
        self._scheduler: Optional[BackgroundScheduler] = None

    def _run_job(self) -> None:
        logger.info("Scheduler triggered run-once")
        try:
            summary = run_once(self._config_path, regions_dir=self._regions_dir)
            logger.info(
                "Run %s done: quotes=%d deals=%d errors=%d",
                summary.run_id, summary.quote_count, summary.deal_count, len(summary.errors),
            )
        except Exception:
            logger.error("Scheduled run failed", exc_info=True)

    def start(self) -> None:
        if self._scheduler and self._scheduler.running:
            logger.warning("Scheduler already running")
            return
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self._run_job,
            trigger=IntervalTrigger(hours=self._interval),
            id=JOB_ID,
            name="Hourly flight deal scan",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Scheduler started (interval=%dh)", self._interval)

    def stop(self) -> None:
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    @property
    def is_running(self) -> bool:
        return bool(self._scheduler and self._scheduler.running)

    def run_now(self) -> None:
        """Manually trigger one run outside the schedule."""
        self._run_job()
