#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
WORKDIR = SCRIPT_DIR.parent
PROMPT_FILE = Path(
    os.environ.get(
        "PROMPT_FILE_OVERRIDE",
        SCRIPT_DIR / "hourly_flight_web_search_terminal_prompt.txt",
    )
)


def resolve_codex_bin() -> str:
    codex_bin = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not codex_bin:
        raise RuntimeError("Could not find `codex` in PATH. Set CODEX_BIN explicitly.")
    return codex_bin


def main() -> int:
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    cmd = [
        resolve_codex_bin(),
        "exec",
        "-C",
        str(WORKDIR),
        "-m",
        os.environ.get("CODEX_MODEL", "gpt-5.4"),
        "-s",
        "workspace-write",
        "--dangerously-bypass-approvals-and-sandbox",
        "-c",
        'model_reasoning_effort="medium"',
        prompt,
    ]
    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"hourly_flight_web_search_terminal.py failed: {exc}", file=sys.stderr)
        raise
