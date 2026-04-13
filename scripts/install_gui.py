#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv_gui"
CONFIG_PATH = ROOT / "config" / "config.yaml"
LOCAL_SEARCH_CONFIG_PATH = ROOT / "config" / "local_web_search.yaml"


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, cwd=ROOT, env=env)


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_venv() -> None:
    if not VENV_DIR.exists():
        print(f"[install] creating virtualenv at {VENV_DIR}")
        try:
            venv.EnvBuilder(with_pip=True).create(VENV_DIR)
            return
        except BaseException as exc:
            if VENV_DIR.exists():
                shutil.rmtree(VENV_DIR, ignore_errors=True)
            print(f"[install] stdlib venv failed: {exc}")
        if shutil.which("uv"):
            print("[install] retrying with `uv venv`")
            run(["uv", "venv", str(VENV_DIR), "--python", sys.executable, "--seed"])
            return
        print("[install] retrying with `virtualenv` module")
        run([sys.executable, "-m", "pip", "install", "--user", "virtualenv"])
        run([sys.executable, "-m", "virtualenv", str(VENV_DIR)])


def install_requirements(python_bin: Path) -> None:
    pip_probe = subprocess.run(
        [str(python_bin), "-m", "pip", "--version"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if pip_probe.returncode == 0:
        run([str(python_bin), "-m", "pip", "install", "-U", "pip"])
        run([str(python_bin), "-m", "pip", "install", "-e", ".[dev]"])
        return
    if shutil.which("uv"):
        print("[install] venv has no pip; retrying install with `uv pip`")
        run(["uv", "pip", "install", "--python", str(python_bin), "-e", ".[dev]"])
        return
    raise RuntimeError("Virtual environment was created without pip, and `uv` is unavailable.")


def ensure_files() -> None:
    if not CONFIG_PATH.exists():
        shutil.copy2(ROOT / "config" / "config.example.yaml", CONFIG_PATH)
        print(f"[install] created {CONFIG_PATH}")
    if not LOCAL_SEARCH_CONFIG_PATH.exists():
        shutil.copy2(ROOT / "config" / "local_web_search.example.yaml", LOCAL_SEARCH_CONFIG_PATH)
        print(f"[install] created {LOCAL_SEARCH_CONFIG_PATH}")


def main() -> int:
    ensure_venv()
    python_bin = venv_python()
    install_requirements(python_bin)
    ensure_files()
    print("")
    print("[install] GUI runtime is ready.")
    print(f"[install] Next: {python_bin} scripts/launch_gui.py")
    print("[install] Then open http://127.0.0.1:8000 and finish setup in the GUI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
