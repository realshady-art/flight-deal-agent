# flight-deal-agent

A flight monitoring project that can run in two modes:

- a traditional pipeline with collectors, storage, rules, and notifications
- a local Codex-powered web-search dashboard that refreshes hourly and shows the current best fares

Repository:
`https://github.com/realshady-art/flight-deal-agent`

## Current Product State

The current primary user-facing flow is the local dashboard:

- server-hosted FastAPI dashboard
- hourly server-side searches using local `codex exec`
- web search only for the dashboard workflow
- no paid flight API required for the dashboard
- fixed Vancouver-area origin scope by default: `YVR` and `YXX`
- fixed Top 10 display board
- optional manual `Start search` trigger for testing

The older API-backed collectors are still in the repository and remain usable for development:

- `stub`
- `amadeus`
- `searchapi`

## What The Dashboard Does

The dashboard is intended to be a read-only display board, not a parameter control panel.

It now does the following:

- runs hourly on the server host
- uses the installed `flight-hourly-web-search` skill
- searches all configured origin airports, not just one
- aggregates, deduplicates, sorts, and displays the current Top 10 routes
- shows route labels as `City (IATA) ↔ City (IATA)`
- places a visible fare-source link at the top of each real route card
- keeps `Start search` independent from the hourly scheduler

Default dashboard search scope:

- origin airports: `YVR`, `YXX`
- destination scope: United States and Canada
- top routes shown: `10`
- refresh cadence: `1 hour`

## Status Summary

### Working

- FastAPI server
- local GUI / dashboard
- hourly local search scheduler
- local `codex exec` search runner
- multi-origin fan-out across `YVR` and `YXX`
- fixed Top 10 board
- recent run log
- installer and launcher scripts
- pytest coverage for API and local search paths

### Still Out Of Scope

- native desktop installer packages such as `.dmg` or `.msi`
- authentication and user-level permissions
- production-grade deployment packaging
- Telegram and email notifications in the local dashboard flow
- cost-controlled production flight search at large scale

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/realshady-art/flight-deal-agent.git
cd flight-deal-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

### 2. Run tests

```bash
pytest -v
```

### 3. Install the local dashboard runtime

```bash
python3 scripts/install_gui.py
```

### 4. Launch the dashboard on the current machine

```bash
python3 scripts/launch_gui.py
```

Then open:

```text
http://127.0.0.1:8000
```

### 5. Launch the dashboard as a shared server

If you want other machines to open the same board while all searches still run on this host:

```bash
python3 scripts/install_gui.py
python3 scripts/launch_gui.py --public --host 0.0.0.0 --port 8000
```

Other clients should then open:

```text
http://<server-host-ip>:8000
```

In this mode:

- the GUI runs on the current host
- the hourly scheduler runs on the current host
- `Start search` runs on the current host
- local `codex exec` also runs on the current host

## Dashboard Runtime Requirements

The dashboard flow does not require a SearchApi key, but it does require:

- Python 3.9+
- a working local `codex` CLI
- a machine where `codex exec` can perform web search successfully

If `codex` is not on `PATH`, set:

```bash
export CODEX_BIN=/absolute/path/to/codex
```

## Important Dashboard Behavior

### Read-only mode

The public dashboard is designed to behave as a read-only board.

That means:

- no provider editing
- no API key editing
- no interval editing
- no scheduler start/stop controls in the UI

The only manual action intentionally left available is:

- `Start search`

This is for testing and on-demand refresh only.

### Top 10 is fixed

For the dashboard workflow, `top_n` is pinned to `10` at runtime.

That pin is enforced in:

- config load
- config save
- installer-generated defaults
- rendering logic

### Origin scope is fixed to Vancouver-area origins by default

The dashboard currently defaults to:

```yaml
origin_airports:
  - YVR
  - YXX
```

The local search execution path fans out across both origins and then merges results back into one ranked board.

## Local Web Search Scripts

### Terminal-only runner

If you want a local terminal result instead of the dashboard:

```bash
python3 scripts/hourly_flight_web_search_terminal.py
```

This script:

- runs a local search immediately
- prints results to stdout
- writes the run to `data/state/local_web_search_runs.jsonl`

### Chat reminder runner

If you want the old reminder behavior that posts a prompt into chat:

```bash
python3 scripts/hourly_flight_web_search_reminder.py
```

This is a different workflow. It is not the same as the local terminal runner.

## Files You Will Use Most

### Launcher and installer

- `scripts/install_gui.py`
- `scripts/launch_gui.py`

### Local dashboard config

- `config/local_web_search.yaml`

### Local run log

- `data/state/local_web_search_runs.jsonl`

### Prompt / skill assets

- `skills/flight-hourly-web-search/SKILL.md`
- `scripts/hourly_flight_web_search_terminal_prompt.txt`

### Frontend files

- `flight_deal_agent/web/index.html`
- `flight_deal_agent/web/app.js`
- `flight_deal_agent/web/app.css`

### Server-side runtime

- `flight_deal_agent/api.py`
- `flight_deal_agent/local_search.py`

## Legacy Collector Mode

The repository still contains the original collector-based pipeline.

Available providers include:

- `stub`
- `amadeus`
- `searchapi`

These are still useful for development, experiments, or future production work, but the current GUI product direction is the local Codex web-search dashboard.

### Run the old pipeline once

```bash
python -m flight_deal_agent run-once
```

### Check config

```bash
python -m flight_deal_agent check-config
```

### Start the old API and scheduler service

```bash
python -m flight_deal_agent serve
```

## Configuration Notes

### Root `.env`

The project still supports a root `.env` for the legacy collector-based modes.

Examples:

- `SEARCHAPI_API_KEY`
- Amadeus credentials

The current dashboard workflow does not need those keys.

### Local dashboard config example

The dashboard installer will generate or normalize:

```yaml
origin_airports:
  - YVR
  - YXX
destination_scope: United States and Canada
top_n: 10
interval_hours: 1
notes: web search only; no paid API; no browser automation
model: gpt-5.4
reasoning_effort: medium
```

## Testing

The dashboard-related regression suite currently focuses on:

- API behavior
- read-only mode
- manual search trigger behavior
- local search aggregation
- multi-origin execution

Typical command:

```bash
./.venv_gui/bin/python -m pytest -q -s tests/test_api.py tests/test_local_search.py
```

## Troubleshooting

### The board still looks stale after `git pull`

First restart the server:

```bash
python3 scripts/install_gui.py
python3 scripts/launch_gui.py --public --host 0.0.0.0 --port 8000
```

Then hard-refresh the browser.

The GUI now uses cache-busting asset versions and `no-store` responses for the dashboard endpoints, so stale browser state should be much less likely.

### The board shows 10 slots but only some real fares

That means the frontend is working correctly.

If fewer than 10 verified findings were returned for that run, the remaining slots are intentionally rendered as placeholders.

### `YXX` does not appear in the board

Check the latest run log in:

- `data/state/local_web_search_runs.jsonl`

Recent runtime evidence should show:

- `searched_origins: ["YVR", "YXX"]`

If the board still does not show `YXX`, the usual causes are:

- the server process was not restarted after pulling new code
- the board is still showing an older run
- the browser is still showing stale state

### `codex` cannot be found

Set `CODEX_BIN` explicitly:

```bash
export CODEX_BIN=/absolute/path/to/codex
```

## Development Notes

When changing the dashboard behavior, keep these product constraints in mind:

- the GUI is a display board first
- local search is the primary workflow
- public mode must remain read-only except for the manual `Start search` action
- dashboard output should remain stable and visually predictable
- origin scope must stay explicit and visible

## License / Ownership

No separate license file is included in the current repository snapshot. Confirm usage and ownership rules with the project owner before redistribution.
