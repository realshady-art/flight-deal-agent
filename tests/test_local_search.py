from __future__ import annotations

from pathlib import Path

from flight_deal_agent.local_search import LocalSearchRun, run_local_web_search


class DummyCompletedProcess:
    def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_run_local_web_search_extracts_structured_findings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "local_web_search.yaml"
    config_path.write_text(
        "\n".join(
            [
                "origin_airports:",
                '  - "YVR"',
                '  - "YXX"',
                'destination_scope: "美国/加拿大"',
                "top_n: 10",
                "interval_hours: 1",
                'notes: "只用 web search"',
                'model: "gpt-5.4"',
                'reasoning_effort: "medium"',
            ]
        ),
        encoding="utf-8",
    )
    template_path = tmp_path / "prompt.txt"
    template_path.write_text(
        "Use the installed skill with {origin_airports}, {destination_scope}, {top_n}, {notes}",
        encoding="utf-8",
    )
    log_path = tmp_path / "runs.jsonl"

    monkeypatch.setenv("CODEX_BIN", "/usr/bin/codex")

    stdout = """```json
{
  "headline": "Two useful fares this hour",
  "summary": "YYC and LAS look cheapest in current indexed results.",
  "findings": [
    {
      "route": "YVR -> YYC",
      "origin_airport": "YVR",
      "destination_airport": "YYC",
      "price_display": "CA$81 round trip",
      "price_value": 81,
      "currency": "CAD",
      "date_range": "Apr 23-28",
      "source_name": "Google Flights",
      "source_url": "https://example.com/yyc",
      "note": "Short-haul fare still stands out."
    },
    {
      "route": "YVR -> LAS",
      "origin_airport": "YVR",
      "destination_airport": "LAS",
      "price_display": "$113 round trip",
      "price_value": 113,
      "currency": "USD",
      "date_range": "May 10-14",
      "source_name": "Kayak",
      "source_url": "https://example.com/las",
      "note": "Cheap Vegas fare for this window."
    }
  ]
}
```

Short terminal summary.
"""

    def fake_run(cmd, cwd, capture_output, text):  # noqa: ANN001
        return DummyCompletedProcess(stdout=stdout)

    monkeypatch.setattr("flight_deal_agent.local_search.subprocess.run", fake_run)

    run = run_local_web_search(
        workdir=tmp_path,
        config_path=config_path,
        template_path=template_path,
        log_path=log_path,
    )

    assert isinstance(run, LocalSearchRun)
    assert run.status == "ok"
    assert run.headline == "Two useful fares this hour"
    assert run.narrative_summary == "YYC and LAS look cheapest in current indexed results."
    assert len(run.findings) == 2
    assert run.findings[0].route == "YVR -> YYC"
    assert log_path.exists()
