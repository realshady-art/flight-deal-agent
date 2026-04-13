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
        interval_minutes: Optional[int] = None,
    ):
        self._config_path = config_path
        self._regions_dir = regions_dir
        self._interval_hours = interval_hours
        self._interval_minutes = interval_minutes
        self._scheduler: Optional[BackgroundScheduler] = None

    @property
    def interval_label(self) -> str:
        if self._interval_minutes is not None:
            return f"{self._interval_minutes}m"
        return f"{self._interval_hours}h"

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
            trigger=(
                IntervalTrigger(minutes=self._interval_minutes)
                if self._interval_minutes is not None
                else IntervalTrigger(hours=self._interval_hours)
            ),
            id=JOB_ID,
            name="Flight deal scan",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Scheduler started (interval=%s)", self.interval_label)

    def stop(self) -> None:
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def reconfigure(
        self,
        *,
        interval_hours: int,
        interval_minutes: Optional[int] = None,
    ) -> None:
        was_running = self.is_running
        if was_running:
            self.stop()
        self._interval_hours = interval_hours
        self._interval_minutes = interval_minutes
        logger.info("Scheduler reconfigured (interval=%s)", self.interval_label)
        if was_running:
            self.start()

    @property
    def is_running(self) -> bool:
        return bool(self._scheduler and self._scheduler.running)

    def run_now(self) -> None:
        """Manually trigger one run outside the schedule."""
        self._run_job()
