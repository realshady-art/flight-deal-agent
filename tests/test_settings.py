from pathlib import Path

import pytest

from flight_deal_agent.settings import load_app_config, load_region_airports


def test_load_config(tmp_config: Path):
    cfg = load_app_config(tmp_config)
    assert cfg.origin_airports == ["BOS"]
    assert cfg.target_region_id == "test_region"
    assert cfg.currency == "USD"
    assert cfg.collector.provider == "stub"
    assert cfg.thresholds.max_total_price == 5000


def test_load_region(tmp_regions: Path):
    airports = load_region_airports(tmp_regions, "test_region")
    assert airports == ["LHR", "CDG", "FRA"]


def test_missing_region(tmp_regions: Path):
    with pytest.raises(FileNotFoundError):
        load_region_airports(tmp_regions, "nonexistent")
