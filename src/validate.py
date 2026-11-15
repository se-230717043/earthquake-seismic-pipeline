# src/validate.py
import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "earthquake.db")

def run_validations(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    stop_failed = False

    # Check 1: Row count equality (STOP)
    raw_eq_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events").fetchone()[0]
    clean_eq_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events_clean").fetchone()[0]
    distinct_raw_eq_cnt = conn.execute("SELECT COUNT(DISTINCT event_id) FROM earthquake_events").fetchone()[0]
    if distinct_raw_eq_cnt == clean_eq_cnt and clean_eq_cnt <= raw_eq_cnt:
        print(f"PASS cleaned events equal distinct raw events ({clean_eq_cnt}; raw snapshots={raw_eq_cnt})")
    else:
        print(f"STOP cleaned event count mismatch ({clean_eq_cnt} != {distinct_raw_eq_cnt} distinct raw)")
        stop_failed = True

    # Check 1b: M4 minimum distinct valid event count (STOP)
    if clean_eq_cnt >= 1000:
        print(f"PASS M4 minimum event count satisfied ({clean_eq_cnt} >= 1000)")
    else:
        print(f"STOP M4 minimum event count not satisfied ({clean_eq_cnt} < 1000)")
        stop_failed = True

    # Check 2: No below-contract magnitude in cleaned column (STOP)
    below_scope_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events_clean WHERE magnitude < 2.5").fetchone()[0]
    if below_scope_cnt == 0:
        print("PASS cleaned magnitudes satisfy M2.5 collection scope")
    else:
        print(f"STOP found {below_scope_cnt} magnitudes below M2.5 in cleaned layer")
        stop_failed = True

    # Check 3: Foreign Key Integrity (STOP)
    fk_checks = conn.execute("PRAGMA foreign_key_check;").fetchall()
    if len(fk_checks) == 0:
        print("PASS foreign_key_check OK")
    else:
        print(f"STOP foreign_key_check failed with {len(fk_checks)} errors")
        stop_failed = True

    # Check 4: Usable magnitude share (WARN)
    valid_mag_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events_clean WHERE magnitude IS NOT NULL").fetchone()[0]
    share = (valid_mag_cnt / clean_eq_cnt) * 100 if clean_eq_cnt > 0 else 0
    if share >= 85.0:
        print(f"PASS usable magnitude share at least 85% ({share:.1f}%)")
    else:
        print(f"WARN usable magnitude share below 85% ({share:.1f}%)")

    # Check 5: Check coordinate validity (STOP)
    invalid_coords = conn.execute("SELECT COUNT(*) FROM elevation_locations_clean WHERE coordinate_flag = 'invalid_out_of_bounds'").fetchone()[0]
    if invalid_coords == 0:
        print("PASS no out of bounds coordinates (0 invalid)")
    else:
        print(f"STOP found {invalid_coords} out of bounds coordinates")
        stop_failed = True

    # Check 6: Event-to-location mapping retains coordinate identity (STOP)
    mapping = conn.execute("""
        SELECT COUNT(DISTINCT e.location_source_id),
               COUNT(DISTINCT l.latitude || ',' || l.longitude)
        FROM earthquake_events_clean AS e
        JOIN elevation_locations_clean AS l ON e.location_source_id = l.source_id
    """).fetchone()
    if clean_eq_cnt <= 1 or (mapping[0] > 1 and mapping[0] == mapping[1]):
        print(f"PASS event locations are coordinate-specific ({mapping[0]} distinct locations)")
    else:
        print(f"STOP event-to-location mapping collapsed or inconsistent ({mapping})")
        stop_failed = True

    # Check 7: Check for unusual extreme events (WARN)
    unusual_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events_clean WHERE magnitude_flag = 'unusual_high'").fetchone()[0]
    if unusual_cnt > 0:
        print(f"WARN unusual high magnitude events flagged: {unusual_cnt} events >= 8.0")
    else:
        print("PASS no unusual extreme high magnitude events")

    conn.close()

    if stop_failed:
        sys.exit(1)

if __name__ == "__main__":
    run_validations()
