from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from flight_deal_agent import __version__


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_run_once(args: argparse.Namespace) -> None:
    from flight_deal_agent.runner import run_once
    summary = run_once(args.config, regions_dir=args.regions_dir)
    print(
        f"[flight-deal-agent] run={summary.run_id} "
        f"tasks={summary.task_count} api_calls={summary.api_calls} "
        f"quotes={summary.quote_count} deals={summary.deal_count} "
        f"errors={len(summary.errors)}"
    )
    if summary.errors:
        for e in summary.errors:
            print(f"  ERROR: {e}", file=sys.stderr)


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    from flight_deal_agent.api import app, configure
    from flight_deal_agent.scheduler import FlightDealScheduler
    from flight_deal_agent.settings import load_app_config

    config = load_app_config(args.config)
    sched = FlightDealScheduler(
        args.config,
        args.regions_dir,
        interval_hours=config.scheduler.interval_hours,
    )
    configure(args.config, args.regions_dir, sched)

    if not args.no_scheduler:
        sched.start()
        print(
            f"[flight-deal-agent] Scheduler started "
            f"(interval={config.scheduler.interval_hours}h)"
        )

    print(f"[flight-deal-agent] API serving on {config.api.host}:{config.api.port}")
    uvicorn.run(app, host=config.api.host, port=config.api.port, log_level="info")


def cmd_check_config(args: argparse.Namespace) -> None:
    from flight_deal_agent.settings import load_app_config, load_region_airports
    try:
        config = load_app_config(args.config)
        airports = load_region_airports(args.regions_dir, config.target_region_id)
        print(f"Config OK: {args.config}")
        print(f"  origins     : {config.origin_airports}")
        print(f"  region      : {config.target_region_id} ({len(airports)} airports)")
        print(f"  provider    : {config.collector.provider}")
        print(f"  currency    : {config.currency}")
        print(f"  budget/run  : {config.collector.request_budget_per_run}")
        print(f"  db          : {config.storage.sqlite_path}")
        print(f"  channel     : {config.alerts.channel}")
    except Exception as exc:
        print(f"Config ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="航班特价监控 agent")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true")

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "-c", "--config", type=Path, default=Path("config/config.yaml"),
        help="配置文件路径",
    )
    shared.add_argument(
        "--regions-dir", type=Path, default=Path("data/regions"),
        help="区域 YAML 目录",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-once", parents=[shared], help="执行一轮采集+分析+通知")

    serve_p = sub.add_parser("serve", parents=[shared], help="启动 API + 调度器")
    serve_p.add_argument("--no-scheduler", action="store_true", help="仅启动 API，不启动定时调度")

    sub.add_parser("check-config", parents=[shared], help="校验配置")

    args = parser.parse_args()
    _setup_logging(args.verbose)

    handler = {
        "run-once": cmd_run_once,
        "serve": cmd_serve,
        "check-config": cmd_check_config,
    }[args.command]
    handler(args)


if __name__ == "__main__":
    main()
