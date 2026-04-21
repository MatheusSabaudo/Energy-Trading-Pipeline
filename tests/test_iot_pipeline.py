import datetime as dt
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))

from ingestion.iot import solar_producer


def test_panel_ids_match_configured_panel_count():
    assert len(solar_producer.PANEL_IDS) == solar_producer.cfg.PANEL_PARAMS["panels"]


@patch("ingestion.iot.solar_producer.datetime")
@patch("ingestion.iot.solar_producer.build_live_panel_event")
def test_generate_solar_event_uses_turin_model(mock_build_live_panel_event, mock_datetime):
    mock_datetime.now.side_effect = [
        dt.datetime(2026, 4, 12, 12, 0, 0),
        dt.datetime(2026, 4, 12, 12, 0, 0, tzinfo=dt.timezone.utc),
    ]
    mock_build_live_panel_event.return_value = {
        "panel_id": "IoT-Data-Panel-001",
        "panel_power_kw": solar_producer.cfg.PANEL_PARAMS["panel_power_kw"],
        "production_kw": 2.184,
        "temperature_c": 21.4,
        "cloud_factor": 0.88,
        "temp_efficiency": 0.992,
        "status": "active",
        "city": "Turin",
    }

    event = solar_producer.generate_solar_event("IoT-Data-Panel-001")

    assert event["panel_id"] == "IoT-Data-Panel-001"
    assert event["panel_power_kw"] == solar_producer.cfg.PANEL_PARAMS["panel_power_kw"]
    assert event["cloud_factor"] == 0.88
    assert event["production_kw"] > 0
