# src/clean.py
import sqlite3
import os
import csv
from clean_config import (
    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX,
    MAG_MIN_VALID, MAG_UNUSUAL_HIGH, ELEVATION_SENTINEL
)

DB_PATH = os.path.join("data", "earthquake.db")
SCHEMA_PATH = os.path.join("sql", "clean_schema.sql")
MAPPINGS_PATH = os.path.join("data", "mappings", "location_mapping.csv")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_clean_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

def load_mappings(conn):
    if os.path.exists(MAPPINGS_PATH):
        with open(MAPPINGS_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [(r["alias"], r["canonical_name"], r["decided_by"], r["decided_at"], r["note"]) for r in reader]
            conn.executemany("""
                INSERT OR REPLACE INTO location_mapping (alias, canonical_name, decided_by, decided_at, note)
                VALUES (?, ?, ?, ?, ?)
            """, rows)
            print(f"mappings: location_mapping loaded {len(rows)} rows")

def clean_data():
    conn = get_connection()
    try:
        with conn:
            init_clean_schema(conn)
            load_mappings(conn)

            # Clear existing cleaned rows for idempotency
            conn.execute("DELETE FROM elevation_locations_clean;")
            conn.execute("DELETE FROM earthquake_events_clean;")
            conn.execute("DELETE FROM quarantine_clean;")

            # 1. Clean elevation_locations
            raw_locs = conn.execute("SELECT * FROM elevation_locations").fetchall()
            flags_loc = {"ok": 0, "missing_not_reported": 0, "invalid_sentinel": 0, "invalid_out_of_bounds": 0}
            
            for row in raw_locs:
                l_key, s_id, lat, lon, elev, ret_at = row
                
                # Check coordinates
                coord_flag = "ok"
                if lat is None or lon is None:
                    coord_flag = "missing_not_reported"
                elif not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                    coord_flag = "invalid_out_of_bounds"

                # Check elevation
                elev_clean = elev
                elev_flag = "ok"
                if elev is None:
                    elev_flag = "missing_not_reported"
                elif elev == ELEVATION_SENTINEL:
                    elev_clean = None
                    elev_flag = "invalid_sentinel"
                
                flags_loc[elev_flag] += 1

                conn.execute("""
                    INSERT INTO elevation_locations_clean (
                        location_key, source_id_raw, source_id, source_id_flag,
                        latitude_raw, latitude, longitude_raw, longitude, coordinate_flag,
                        elevation_raw, elevation, elevation_flag, retrieved_at
                    ) VALUES (?, ?, ?, 'ok', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (l_key, s_id, s_id, lat, lat, lon, lon, coord_flag, elev, elev_clean, elev_flag, ret_at))

            # 2. Clean earthquake_events
            raw_events = conn.execute("SELECT * FROM earthquake_events").fetchall()
            flags_eq = {"ok": 0, "invalid_negative": 0, "unusual_high": 0, "missing_not_reported": 0}

            for row in raw_events:
                e_id, loc_s_id, mag, place, e_time, ret_at = row
                
                mag_clean = mag
                mag_flag = "ok"
                if mag is None:
                    mag_flag = "missing_not_reported"
                    mag_clean = None
                elif mag < MAG_MIN_VALID:
                    mag_clean = None
                    mag_flag = "invalid_negative"
                elif mag >= MAG_UNUSUAL_HIGH:
                    mag_flag = "unusual_high"

                flags_eq[mag_flag] += 1

                place_clean = place.strip() if place else place
                place_flag = "standardized_text" if place != place_clean else "ok"

                conn.execute("""
                    INSERT INTO earthquake_events_clean (
                        event_id, location_source_id_raw, location_source_id, location_source_id_flag,
                        magnitude_raw, magnitude, magnitude_flag, place_raw, place, place_flag,
                        event_time, retrieved_at
                    ) VALUES (?, ?, ?, 'ok', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (e_id, loc_s_id, loc_s_id, mag, mag_clean, mag_flag, place, place_clean, place_flag, e_time, ret_at))

            # 3. Copy Quarantine
            conn.execute("""
                INSERT INTO quarantine_clean SELECT * FROM quarantine;
            """)

            print(f"elevation_locations_clean: {len(raw_locs)} rows (raw: {len(raw_locs)})")
            print(f"  elevation flags: {flags_loc}")
            print(f"earthquake_events_clean: {len(raw_events)} rows (raw: {len(raw_events)})")
            print(f"  magnitude flags: {flags_eq}")
            print("STATUS: COMPLETE")

    finally:
        conn.close()

if __name__ == "__main__":
    clean_data()