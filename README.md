# OrbitScan

OrbitScan is a flight-deal intelligence dashboard that continuously scans public fare signals, ranks high-value routes, and turns scattered travel results into a clean Top 10 board.

Live demo: https://orbitscan-demo.vercel.app

## Product Idea

Cheap flights are time-sensitive, fragmented, and hard to compare across sources. OrbitScan is designed as a lightweight monitoring layer that repeatedly checks configured origin airports, extracts relevant fare opportunities, and presents the best routes in one readable view.

Instead of asking users to search the same routes manually, OrbitScan keeps the search loop running and highlights the deals most worth checking.

## Core Experience

- Multi-origin monitoring for Vancouver-area airports such as YVR and YXX.
- Ranked Top 10 board based on parsed fare value and route relevance.
- Clear route cards with city labels, price, travel dates, and source links.
- Date-aware filtering so outdated fares do not stay on the board.
- Manual refresh support for quick on-demand checks.
- Server-side run history for comparing recent search results.

## How It Works

1. Search tasks run on a fixed cadence for the configured origin and destination scope.
2. Results are normalized into structured route, price, date, and source fields.
3. Duplicate and expired findings are filtered out.
4. Remaining fares are ranked by price and displayed as a compact deal board.
5. Each card links back to the original source and travel-search pages for follow-up.

## Product Effect

OrbitScan reduces repeated manual checking and makes fare discovery easier to review at a glance. The dashboard is optimized for quick comparison: where the deal is, how much it costs, when it applies, and where to verify it.

## Tech Stack

- Python
- FastAPI
- Local search orchestration
- HTML, CSS, JavaScript
- Structured run logs

## Local Preview

```bash
git clone https://github.com/JeffreyDeng-spec/OrbitScan.git
cd OrbitScan
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 scripts/launch_gui.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Project Focus

OrbitScan is built around a simple product principle: keep the collection process automatic, keep the interface readable, and make every surfaced deal easy to verify.
