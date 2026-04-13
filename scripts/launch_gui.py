#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv_gui"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv_exec() -> None:
    target = venv_python()
    current_prefix = Path(sys.prefix).resolve()
    if current_prefix != VENV_DIR.resolve():
        if not target.exists():
            raise SystemExit(
                "Missing .venv_gui runtime. Run `python3 scripts/install_gui.py` first."
            )
        os.execv(
            str(target),
            [str(target), str(Path(__file__).resolve()), *sys.argv[1:]],
        )


def open_browser_later(url: str, delay: float = 2.0) -> None:
    def _worker() -> None:
        time.sleep(delay)
        commands: list[list[str]] = []
        if sys.platform == "darwin":
            commands.append(["open", url])
        elif os.name == "nt":
            commands.append(["cmd", "/c", "start", "", url])
        else:
            commands.append(["xdg-open", url])
        for command in commands:
            try:
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                continue

    threading.Thread(target=_worker, daemon=True).start()


def main() -> int:
    ensure_venv_exec()
    parser = argparse.ArgumentParser(description="Launch the flight-deal-agent control room")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument(
        "--public",
        action="store_true",
        help="Bind on 0.0.0.0 so other machines can use this server-side Codex runtime.",
    )
    args = parser.parse_args()
    host = "0.0.0.0" if args.public else args.host
    url_host = "127.0.0.1" if host == "0.0.0.0" else host
    url = f"http://{url_host}:{args.port}"
    open_browser_later(url)
    cmd = [
        sys.executable,
        "-m",
        "flight_deal_agent",
        "serve",
        "--no-scheduler",
        "--host",
        host,
        "--port",
        str(args.port),
    ]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
