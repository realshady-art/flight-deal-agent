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
    assert cfg.thresholds.lowest_n_per_run is None
    assert cfg.scheduler.interval_minutes is None


def test_load_region(tmp_regions: Path):
    airports = load_region_airports(tmp_regions, "test_region")
    assert airports == ["LHR", "CDG", "FRA"]


def test_missing_region(tmp_regions: Path):
    with pytest.raises(FileNotFoundError):
        load_region_airports(tmp_regions, "nonexistent")


def test_load_config_with_origin_region_and_minutes(tmp_path: Path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
app:
  name: test
  timezone: UTC
origin_region_id: test_region
target_region_id: test_region
collector:
  provider: stub
scheduler:
  interval_minutes: 10
""".strip(),
        encoding="utf-8",
    )
    cfg = load_app_config(cfg_path)
    assert cfg.origin_airports == []
    assert cfg.origin_region_id == "test_region"
    assert cfg.scheduler.interval_minutes == 10
    assert cfg.scheduler.label == "10m"
