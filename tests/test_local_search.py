from __future__ import annotations

from datetime import date
from pathlib import Path

from flight_deal_agent.local_search import (
    LocalSearchFinding,
    LocalSearchRun,
    parse_travel_dates_in_text,
    retain_findings_forward_dates,
    run_local_web_search,
)


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
        "Use the installed skill with {origin_airports}, {destination_scope}, {top_n}, {notes}, "
        "today={today_iso} {today_long}",
        encoding="utf-8",
    )
    log_path = tmp_path / "runs.jsonl"

    monkeypatch.setenv("CODEX_BIN", "/usr/bin/codex")

    stdout_yvr = """```json
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

    stdout_yxx = """```json
{
  "headline": "One Abbotsford fare this hour",
  "summary": "YXX surfaced a cheap Vegas fare.",
  "findings": [
    {
      "route": "YXX -> LAS",
      "origin_airport": "YXX",
      "destination_airport": "LAS",
      "price_display": "$109 round trip",
      "price_value": 109,
      "currency": "USD",
      "date_range": "May 12-16",
      "source_name": "Kayak",
      "source_url": "https://example.com/yxx-las",
      "note": "Abbotsford still has a useful U.S. fare."
    }
  ]
}
```

Short terminal summary.
"""

    responses = iter(
        [
            DummyCompletedProcess(stdout=stdout_yvr),
            DummyCompletedProcess(stdout=stdout_yxx),
        ]
    )

    def fake_run(cmd, cwd, capture_output, text):  # noqa: ANN001
        return next(responses)

    monkeypatch.setattr("flight_deal_agent.local_search.subprocess.run", fake_run)

    run = run_local_web_search(
        workdir=tmp_path,
        config_path=config_path,
        template_path=template_path,
        log_path=log_path,
    )

    assert isinstance(run, LocalSearchRun)
    assert run.status == "ok"
    assert run.searched_origins == ["YVR", "YXX"]
    assert run.missing_origins == []
    assert "Searched origins: YVR, YXX." in (run.coverage_note or "")
    assert run.narrative_summary is not None
    assert "YVR: YYC and LAS look cheapest in current indexed results." in run.narrative_summary
    assert "YXX: YXX surfaced a cheap Vegas fare." in run.narrative_summary
    assert len(run.findings) == 3
    assert run.findings[0].route == "YVR -> YYC"
    assert any(finding.origin_airport == "YXX" for finding in run.findings)
    assert log_path.exists()


def test_retain_findings_drops_past_iso_dates() -> None:
    today = date(2026, 4, 14)
    future = LocalSearchFinding(
        route="YVR -> YYC",
        origin_airport="YVR",
        destination_airport="YYC",
        price_display="CA$200",
        date_range="2026-06-01 / 2026-06-08",
        source_name="x",
        source_url="https://example.com/a",
        note="",
    )
    past = LocalSearchFinding(
        route="YVR -> LAS",
        origin_airport="YVR",
        destination_airport="LAS",
        price_display="CA$150",
        date_range="2026-01-10 to 2026-01-17",
        source_name="x",
        source_url="https://example.com/b",
        note="",
    )
    kept = retain_findings_forward_dates([future, past], today=today)
    assert len(kept) == 1
    assert kept[0].destination_airport == "YYC"


def test_retain_findings_drops_unqualified_month_names() -> None:
    today = date(2026, 4, 14)
    march = LocalSearchFinding(
        route="YVR -> LAS",
        origin_airport="YVR",
        destination_airport="LAS",
        price_display="CA$150",
        date_range="Mar 3 - Mar 9",
        source_name="x",
        source_url="https://example.com/c",
        note="",
    )
    may = LocalSearchFinding(
        route="YVR -> LAS",
        origin_airport="YVR",
        destination_airport="LAS",
        price_display="CA$160",
        date_range="May 10-14",
        source_name="x",
        source_url="https://example.com/d",
        note="",
    )
    kept = retain_findings_forward_dates([march, may], today=today)
    assert len(kept) == 1
    assert "May" in kept[0].date_range


def test_parse_travel_dates_in_text_finds_iso_and_english() -> None:
    blob = "Trip 2026-05-01 and back2026-05-10; also see Apr 20-25"
    ds = parse_travel_dates_in_text(blob, anchor_year=2026)
    assert date(2026, 5, 1) in ds
    assert date(2026, 5, 10) in ds
    assert date(2026, 4, 20) in ds
    assert date(2026, 4, 25) in ds
