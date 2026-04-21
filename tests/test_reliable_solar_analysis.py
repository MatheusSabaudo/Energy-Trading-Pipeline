import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfoNotFoundError

sys.path.append(str(Path(__file__).parent.parent))

from solar_analysis_data.reliable_analysis import run_reliable_analysis
from solar_analysis_data.turin_model import (
    EuropeRomeFallbackTZ,
    TurinSimulationConfig,
    generate_hourly_dataset,
)


def test_generate_hourly_dataset_covers_full_year_with_day_night_behavior():
    config = TurinSimulationConfig(system_size_kw=3.0)
    rows = generate_hourly_dataset(2026, config=config)

    january_midnight = next(row for row in rows if row["date"] == "2026-01-15" and row["hour"] == 0)
    january_noon = next(row for row in rows if row["date"] == "2026-01-15" and row["hour"] == 12)
    june_noon = next(row for row in rows if row["date"] == "2026-06-15" and row["hour"] == 12)

    assert len(rows) == 365 * 24
    assert january_midnight["production_kw"] == 0
    assert june_noon["production_kw"] > january_noon["production_kw"]
    assert june_noon["solar_elevation_deg"] > january_noon["solar_elevation_deg"]


def test_run_reliable_analysis_writes_outputs_and_consistent_metrics():
    result = run_reliable_analysis(2026)
    summary = result["summary"]
    current = summary["current_system"]
    optimal = summary["optimal_system"]

    assert result["dataset_path"].exists()
    assert result["monthly_path"].exists()
    assert result["summary_path"].exists()
    assert result["report_path"].exists()
    assert current["year_one"]["annual_production_kwh"] > 2000
    assert 0 <= current["year_one"]["self_consumption_pct"] <= 100
    assert 0 <= optimal["year_one"]["demand_coverage_pct"] <= 100
    assert len(summary["monthly_summary"]) == 12


def test_turin_timezone_falls_back_without_tzdata():
    with patch("solar_analysis_data.turin_model.ZoneInfo", side_effect=ZoneInfoNotFoundError("missing tzdata")):
        config = TurinSimulationConfig()
        tz = config.tzinfo

    assert isinstance(tz, EuropeRomeFallbackTZ)
    winter = datetime(2026, 1, 15, 12, 0, tzinfo=tz)
    summer = datetime(2026, 7, 15, 12, 0, tzinfo=tz)
    assert winter.utcoffset() == timedelta(hours=1)
    assert summer.utcoffset() == timedelta(hours=2)
