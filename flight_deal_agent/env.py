"""Load environment variables from .env (repo root + current working directory)."""
from __future__ import annotations

from pathlib import Path

_loaded = False


def load_app_env() -> None:
    """Idempotent: load `.env` from package repo root, then from cwd."""
    global _loaded
    if _loaded:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")
    load_dotenv()
    _loaded = True


def reset_env_loader_for_tests() -> None:
    global _loaded
    _loaded = False
