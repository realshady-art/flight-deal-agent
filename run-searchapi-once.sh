#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

./.venv/bin/python -m flight_deal_agent check-config
./.venv/bin/python -m flight_deal_agent run-once
