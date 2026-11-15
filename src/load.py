"""Idempotently load raw API snapshots into the M2 SQLite schema."""

import glob
import json
import os
from datetime import datetime, timezone

from db import connect
from locations import source_id_for_coordinates

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")


def init_db(con):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as handle:
        con.executescript(handle.read())


def _upsert_location(con, latitude, longitude, elevation, retrieved_at):
    source_id = source_id_for_coordinates(latitude, longitude)
    con.execute("""
        INSERT INTO elevation_locations (source_id, latitude, longitude, elevation, retrieved_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(source_id) DO UPDATE SET
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            elevation=COALESCE(excluded.elevation, elevation_locations.elevation),
            retrieved_at=MAX(excluded.retrieved_at, elevation_locations.retrieved_at)
    """, (source_id, float(latitude), float(longitude), elevation, retrieved_at))
    return source_id


def load_data(db_path=None, raw_dir=RAW_DIR):
    con = connect(db_path) if db_path else connect()
    init_db(con)
    files_read_count = locations_count = events_count = quarantined_count = 0

    for filepath in sorted(glob.glob(os.path.join(raw_dir, "elevation", "*.json"))):
        files_read_count += 1
        retrieved_at = os.path.basename(filepath).replace(".json", "")
        with open(filepath, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        with con:
            if isinstance(data.get("locations"), list):
                for location in data["locations"]:
                    _upsert_location(con, location["latitude"], location["longitude"],
                                     location.get("elevation"), retrieved_at)
                    locations_count += 1
            else:
                # Backwards compatibility for the original single-coordinate payload.
                latitudes = data.get("latitude", [38.42])
                longitudes = data.get("longitude", [27.14])
                elevations = data.get("elevation", [None])
                if not isinstance(latitudes, list):
                    latitudes = [latitudes]
                if not isinstance(longitudes, list):
                    longitudes = [longitudes]
                if not isinstance(elevations, list):
                    elevations = [elevations]
                for latitude, longitude, elevation in zip(latitudes, longitudes, elevations):
                    _upsert_location(con, latitude, longitude, elevation, retrieved_at)
                    locations_count += 1

    for filepath in sorted(glob.glob(os.path.join(raw_dir, "earthquake", "*.json"))):
        files_read_count += 1
        retrieved_at = os.path.basename(filepath).replace(".json", "")
        with open(filepath, "r", encoding="utf-8") as handle:
            features = json.load(handle).get("features", [])
        for feature in features:
            props = feature.get("properties", {})
            event_id, magnitude, place = feature.get("id"), props.get("mag"), props.get("place")
            time_ms = props.get("time")
            coordinates = (feature.get("geometry") or {}).get("coordinates") or []
            longitude = coordinates[0] if len(coordinates) >= 2 else None
            latitude = coordinates[1] if len(coordinates) >= 2 else None
            event_time = (
                datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if time_ms is not None else None
            )
            coordinate_valid = (
                latitude is not None and longitude is not None
                and -90 <= latitude <= 90 and -180 <= longitude <= 180
            )
            if not event_id or magnitude is None or not event_time or not coordinate_valid:
                with con:
                    con.execute("""
                        INSERT INTO quarantine (source_name, raw_record, reason, quarantined_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(source_name, raw_record, reason, quarantined_at) DO NOTHING
                    """, ("USGS", json.dumps(feature, sort_keys=True),
                          "Missing/invalid critical fields", retrieved_at))
                quarantined_count += 1
                continue
            with con:
                location_source_id = _upsert_location(con, latitude, longitude, None, retrieved_at)
                con.execute("""
                    INSERT INTO earthquake_events
                        (event_id, location_source_id, magnitude, place, event_time, retrieved_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id, retrieved_at) DO UPDATE SET
                        location_source_id=excluded.location_source_id,
                        magnitude=excluded.magnitude,
                        place=excluded.place,
                        event_time=excluded.event_time
                """, (event_id, location_source_id, float(magnitude), place, event_time, retrieved_at))
            events_count += 1

    fk_check = con.execute("PRAGMA foreign_key_check").fetchall()
    print("================ Run Summary ================")
    print(f"files read: {files_read_count}")
    print(f"locations processed: {locations_count}")
    print(f"events processed: {events_count}")
    print(f"quarantined: {quarantined_count}")
    print(f"foreign_key_check: {'OK' if not fk_check else f'FAIL ({len(fk_check)} errors)'}")
    print("STATUS: COMPLETE")
    print("=============================================")
    con.close()


if __name__ == "__main__":
    load_data()
