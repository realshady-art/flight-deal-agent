#!/usr/bin/env python3
from __future__ import annotations

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
        os.execv(str(target), [str(target), str(Path(__file__).resolve())])


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
    url = "http://127.0.0.1:8000"
    open_browser_later(url)
    cmd = [
        sys.executable,
        "-m",
        "flight_deal_agent",
        "serve",
    ]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
