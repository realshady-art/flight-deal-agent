#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$("${ROOT_DIR}/scripts/ensure-runtime-python.sh")"

cd "${ROOT_DIR}"
if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  printf '%s\n' "Created .env from .env.example. Fill SEARCHAPI_API_KEY first, then rerun." >&2
  exit 1
fi

if ! grep -Eq '^SEARCHAPI_API_KEY=.+$' "${ROOT_DIR}/.env"; then
  printf '%s\n' "Missing SEARCHAPI_API_KEY in .env" >&2
  exit 1
fi

exec "${PYTHON_BIN}" -m flight_deal_agent serve -c config/config.yaml --regions-dir data/regions
