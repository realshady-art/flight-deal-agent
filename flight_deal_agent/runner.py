"""run_once: the main single-pass pipeline."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flight_deal_agent.env import load_app_env
from flight_deal_agent.analyst import evaluate_deals
from flight_deal_agent.collector import collect_quotes
from flight_deal_agent.models import RunSummary
from flight_deal_agent.notifier import notify_deals
from flight_deal_agent.orchestrator import plan_tasks
from flight_deal_agent.settings import AppConfig, load_app_config, load_region_airports
from flight_deal_agent.storage import init_db, log_run, persist_quotes

logger = logging.getLogger(__name__)


def run_once(
    config_path: Path,
    *,
    regions_dir: Path,
) -> RunSummary:
    load_app_env()
    run_id = uuid.uuid4().hex[:12]
    started = datetime.now(tz=timezone.utc)
    errors = []

    config = load_app_config(config_path)
    db_path = Path(config.storage.sqlite_path)
    init_db(db_path)

    destination_airports = load_region_airports(regions_dir, config.target_region_id)
    origin_airports = (
        load_region_airports(regions_dir, config.origin_region_id)
        if config.origin_region_id
        else config.origin_airports
    )
    tasks = plan_tasks(config, origin_airports, destination_airports)
    logger.info("[%s] planned %d tasks", run_id, len(tasks))

    try:
        quotes, api_calls = collect_quotes(config, tasks, run_id)
    except Exception as exc:
        logger.error("Collection failed: %s", exc, exc_info=True)
        quotes, api_calls = [], 0
        errors.append(str(exc))

    persisted = persist_quotes(db_path, quotes)
    logger.info("[%s] persisted %d quotes", run_id, persisted)

    try:
        deals = evaluate_deals(config, quotes, db_path)
    except Exception as exc:
        logger.error("Analysis failed: %s", exc, exc_info=True)
        deals = []
        errors.append(str(exc))

    try:
        notify_deals(config, deals, db_path)
    except Exception as exc:
        logger.error("Notification failed: %s", exc, exc_info=True)
        errors.append(str(exc))

    finished = datetime.now(tz=timezone.utc)
    summary = RunSummary(
        run_id=run_id,
        started_at=started,
        finished_at=finished,
        task_count=len(tasks),
        api_calls=api_calls,
        quote_count=len(quotes),
        deal_count=len(deals),
        errors=errors,
    )
    try:
        log_run(db_path, summary)
    except Exception:
        logger.warning("Failed to log run", exc_info=True)

    return summary
