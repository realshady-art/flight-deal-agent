#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv_gui"
CONFIG_PATH = ROOT / "config" / "config.yaml"
LOCAL_SEARCH_CONFIG_PATH = ROOT / "config" / "local_web_search.yaml"
SKILL_SOURCE_DIR = ROOT / "skills" / "flight-hourly-web-search"


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


def normalize_local_search_config() -> None:
    raw = {}
    if LOCAL_SEARCH_CONFIG_PATH.exists():
        raw = yaml.safe_load(LOCAL_SEARCH_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    origin_airports = raw.get("origin_airports")
    if not isinstance(origin_airports, list):
        legacy_origin = raw.get("origin_airport")
        origin_airports = [legacy_origin] if legacy_origin else ["YVR"]
    normalized_origins: list[str] = []
    for airport in [*(origin_airports or []), "YVR", "YXX"]:
        airport_code = str(airport).strip().upper()
        if airport_code and airport_code not in normalized_origins:
            normalized_origins.append(airport_code)
    raw["origin_airports"] = normalized_origins
    raw.pop("origin_airport", None)
    raw["top_n"] = 10
    raw["interval_hours"] = 1
    raw.setdefault("destination_scope", "美国/加拿大")
    raw.setdefault("notes", "只用 web search，不用付费 API，不用浏览器自动化。")
    raw.setdefault("model", "gpt-5.4")
    raw.setdefault("reasoning_effort", "medium")
    LOCAL_SEARCH_CONFIG_PATH.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"[install] normalized {LOCAL_SEARCH_CONFIG_PATH} to hourly Top 10 dashboard mode")


def install_skill() -> None:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    skill_target = codex_home / "skills" / "flight-hourly-web-search"
    skill_target.parent.mkdir(parents=True, exist_ok=True)
    if skill_target.exists():
        shutil.rmtree(skill_target)
    shutil.copytree(SKILL_SOURCE_DIR, skill_target)
    print(f"[install] installed skill at {skill_target}")


def main() -> int:
    ensure_venv()
    python_bin = venv_python()
    install_requirements(python_bin)
    ensure_files()
    normalize_local_search_config()
    install_skill()
    print("")
    print("[install] GUI runtime is ready.")
    print(f"[install] Next: {python_bin} scripts/launch_gui.py")
    print("[install] Local-only mode: python3 scripts/launch_gui.py")
    print("[install] Shared server mode: python3 scripts/launch_gui.py --public")
    print("[install] Then open http://127.0.0.1:8000 (or the server IP) and finish setup in the GUI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
