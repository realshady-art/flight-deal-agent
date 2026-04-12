#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_VENV="${ROOT_DIR}/.venv"
LEGACY_VENV="${ROOT_DIR}/.venv_uv"

is_usable_python() {
  local candidate="$1"
  [[ -x "${candidate}" ]] || return 1
  "${candidate}" - <<'PY' >/dev/null 2>&1
import importlib.util
import sys

required = ["yaml", "pydantic", "httpx", "apscheduler", "fastapi"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
raise SystemExit(0 if not missing else 1)
PY
}

if is_usable_python "${DEFAULT_VENV}/bin/python"; then
  printf '%s\n' "${DEFAULT_VENV}/bin/python"
  exit 0
fi

if is_usable_python "${LEGACY_VENV}/bin/python"; then
  printf '%s\n' "${LEGACY_VENV}/bin/python"
  exit 0
fi

if command -v uv >/dev/null 2>&1; then
  uv venv "${DEFAULT_VENV}" >/dev/null
  uv pip install --python "${DEFAULT_VENV}/bin/python" -e "${ROOT_DIR}" >/dev/null
  printf '%s\n' "${DEFAULT_VENV}/bin/python"
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  python3 -m venv "${DEFAULT_VENV}"
  "${DEFAULT_VENV}/bin/python" -m pip install -U pip >/dev/null
  "${DEFAULT_VENV}/bin/python" -m pip install -e "${ROOT_DIR}" >/dev/null
  printf '%s\n' "${DEFAULT_VENV}/bin/python"
  exit 0
fi

printf '%s\n' "No usable Python runtime found. Install uv or python3 with venv support." >&2
exit 1
