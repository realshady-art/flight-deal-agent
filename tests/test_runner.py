from pathlib import Path

from flight_deal_agent.runner import run_once


def test_run_once_stub(tmp_config: Path, tmp_regions: Path):
    summary = run_once(tmp_config, regions_dir=tmp_regions)
    assert summary.task_count > 0
    assert summary.quote_count == 0
    assert summary.deal_count == 0
    assert len(summary.errors) == 0
