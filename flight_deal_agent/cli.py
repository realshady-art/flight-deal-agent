from __future__ import annotations

import argparse
from pathlib import Path

from flight_deal_agent import __version__
from flight_deal_agent.runner import run_once


def main() -> None:
    parser = argparse.ArgumentParser(
        description="航班特价监控 agent骨架：run-once 与配置校验",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run-once", help="执行一轮采集 + 分析 + 通知（默认采集器为 stub）")
    run_p.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="配置文件路径",
    )
    run_p.add_argument(
        "--regions-dir",
        type=Path,
        default=Path("data/regions"),
        help="区域 YAML 所在目录",
    )
    run_p.add_argument(
        "--demo-notification",
        action="store_true",
        help="不调用真实采集，插入一条演示 deal 验证通知输出",
    )

    args = parser.parse_args()
    if args.command == "run-once":
        summary = run_once(
            args.config,
            regions_dir=args.regions_dir,
            demo_notification=args.demo_notification,
        )
        print(
            f"[flight-deal-agent] 完成：tasks={summary.task_count} "
            f"quotes={summary.quote_count} deals={summary.deal_count}"
        )


if __name__ == "__main__":
    main()
