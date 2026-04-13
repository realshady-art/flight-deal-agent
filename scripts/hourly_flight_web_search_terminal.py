#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORKDIR = SCRIPT_DIR.parent
if str(WORKDIR) not in sys.path:
    sys.path.insert(0, str(WORKDIR))

from flight_deal_agent.local_search import run_local_web_search

PROMPT_FILE = Path(os.environ.get("PROMPT_FILE_OVERRIDE", SCRIPT_DIR / "hourly_flight_web_search_terminal_prompt.txt"))
CONFIG_FILE = Path(os.environ.get("LOCAL_WEB_SEARCH_CONFIG", WORKDIR / "config" / "local_web_search.yaml"))
LOG_FILE = Path(os.environ.get("LOCAL_WEB_SEARCH_LOG", WORKDIR / "data" / "state" / "local_web_search_runs.jsonl"))


def main() -> int:
    run = run_local_web_search(
        workdir=WORKDIR,
        config_path=CONFIG_FILE,
        template_path=PROMPT_FILE,
        log_path=LOG_FILE,
    )
    if run.output:
        print(run.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"hourly_flight_web_search_terminal.py failed: {exc}", file=sys.stderr)
        raise
