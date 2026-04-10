from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flight_deal_agent.analyst import evaluate_deals
from flight_deal_agent.collector import collect_quotes
from flight_deal_agent.notifier import notify_deals
from flight_deal_agent.orchestrator import plan_tasks
from flight_deal_agent.settings import AppConfig, load_app_config, load_region_airports
from flight_deal_agent.storage import persist_quotes


@dataclass
class RunSummary:
    task_count: int
    quote_count: int
    deal_count: int


def run_once(
    config_path: Path,
    *,
    regions_dir: Path,
    demo_notification: bool = False,
) -> RunSummary:
    config = load_app_config(config_path)
    airports = load_region_airports(regions_dir, config.target_region_id)
    tasks = plan_tasks(config, airports)

    if demo_notification:
        from flight_deal_agent.collector import make_demo_quote
        from flight_deal_agent.models import DealCandidate

        if not tasks:
            quotes = []
        else:
            quotes = [make_demo_quote(tasks[0], config.currency)]
        deals = [
            DealCandidate(quote=quotes[0], reason="演示：验证 notifier 与配置加载")
        ] if quotes else []
        notify_deals(config, deals)
        return RunSummary(task_count=len(tasks), quote_count=len(quotes), deal_count=len(deals))

    quotes = collect_quotes(config, tasks)
    db_path = Path(config.storage.sqlite_path)
    persist_quotes(db_path, quotes)
    deals = evaluate_deals(config, quotes)
    notify_deals(config, deals)
    return RunSummary(task_count=len(tasks), quote_count=len(quotes), deal_count=len(deals))
