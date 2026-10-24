import os
import glob
import json
from datetime import datetime, timezone
from db import connect

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")

def init_db(con):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    con.executescript(schema_sql)

def load_data(db_path=None):
    con = connect(db_path) if db_path else connect()
    init_db(con)

    files_read_count = 0
    locations_count = 0
    events_count = 0
    quarantined_count = 0

    # 1. Elevation Data (Entity Table) Yükleme
    elevation_files = sorted(glob.glob(os.path.join(RAW_DIR, "elevation", "*.json")))
    for filepath in elevation_files:
        files_read_count += 1
        retrieved_at = os.path.basename(filepath).replace(".json", "")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        source_id = "loc_izmir_38.42_27.14"
        latitude = 38.42
        longitude = 27.14
        elevation = data.get("elevation", [None])[0] if isinstance(data.get("elevation"), list) else data.get("elevation")

        with con:
            con.execute("""
                INSERT INTO elevation_locations (source_id, latitude, longitude, elevation, retrieved_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    elevation=excluded.elevation,
                    retrieved_at=excluded.retrieved_at
            """, (source_id, latitude, longitude, elevation, retrieved_at))
            locations_count += 1

    # 2. Earthquake Data (Event Table) Upload
    earthquake_files = sorted(glob.glob(os.path.join(RAW_DIR, "earthquake", "*.json")))
    for filepath in earthquake_files:
        files_read_count += 1
        retrieved_at = os.path.basename(filepath).replace(".json", "")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            event_id = feat.get("id")
            mag = props.get("mag")
            place = props.get("place")
            time_ms = props.get("time")

            event_time = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if time_ms else None

            # Missing Data Check (Route to quarantine)
            if not event_id or mag is None or not event_time:
                with con:
                    con.execute("""
                        INSERT INTO quarantine (source_name, raw_record, reason, quarantined_at)
                        VALUES (?, ?, ?, ?)
                    """, ("USGS", json.dumps(feat), "Missing critical fields", retrieved_at))
                    quarantined_count += 1
                continue

            location_source_id = "loc_izmir_38.42_27.14"

            with con:
                con.execute("""
                    INSERT INTO earthquake_events (event_id, location_source_id, magnitude, place, event_time, retrieved_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id, retrieved_at) DO UPDATE SET
                        magnitude=excluded.magnitude,
                        place=excluded.place,
                        event_time=excluded.event_time
                """, (event_id, location_source_id, float(mag), place, event_time, retrieved_at))
                events_count += 1

    # Foreign Key Constraint Check
    fk_check = con.execute("PRAGMA foreign_key_check;").fetchall()
    fk_status = "OK" if len(fk_check) == 0 else f"FAIL ({len(fk_check)} errors)"

    print("================ Run Summary ================")
    print(f"files read: {files_read_count}")
    print(f"locations: {locations_count} in database")
    print(f"events: {events_count} in database")
    print(f"quarantined: {quarantined_count} records")
    print(f"foreign_key_check: {fk_status}")
    print("STATUS: COMPLETE")
    print("=============================================")

if __name__ == "__main__":
    load_data()