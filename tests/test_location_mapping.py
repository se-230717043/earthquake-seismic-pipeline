import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clean import clean_data
from load import load_data
from locations import source_id_for_coordinates


def write_fixture(raw_dir):
    (raw_dir / "earthquake").mkdir(parents=True)
    (raw_dir / "elevation").mkdir(parents=True)
    timestamp = "20261115T120000Z"
    events = {
        "features": [
            {"id": "a", "properties": {"mag": 3.1, "place": "A", "time": 1794744000000},
             "geometry": {"coordinates": [27.14, 38.42, 10]}},
            {"id": "b", "properties": {"mag": 4.2, "place": "B", "time": 1794747600000},
             "geometry": {"coordinates": [-122.3, 47.6, 8]}},
        ]
    }
    elevations = {"locations": [
        {"latitude": 38.42, "longitude": 27.14, "elevation": 20.0},
        {"latitude": 47.6, "longitude": -122.3, "elevation": 110.0},
    ]}
    (raw_dir / "earthquake" / f"{timestamp}.json").write_text(json.dumps(events), encoding="utf-8")
    (raw_dir / "elevation" / f"{timestamp}.json").write_text(json.dumps(elevations), encoding="utf-8")


def test_events_keep_actual_coordinates_and_load_is_idempotent(tmp_path):
    raw_dir = tmp_path / "raw"
    db_path = tmp_path / "earthquake.db"
    write_fixture(raw_dir)
    load_data(str(db_path), str(raw_dir))
    load_data(str(db_path), str(raw_dir))
    clean_data(str(db_path))
    con = sqlite3.connect(db_path)
    rows = con.execute("""
        SELECT e.event_id, e.location_source_id, l.latitude, l.longitude, l.elevation
        FROM earthquake_events AS e
        JOIN elevation_locations AS l ON l.source_id = e.location_source_id
        ORDER BY e.event_id
    """).fetchall()
    assert rows == [
        ("a", source_id_for_coordinates(38.42, 27.14), 38.42, 27.14, 20.0),
        ("b", source_id_for_coordinates(47.6, -122.3), 47.6, -122.3, 110.0),
    ]
    assert con.execute("SELECT COUNT(*) FROM earthquake_events").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM earthquake_events_clean").fetchone()[0] == 2
    con.close()
