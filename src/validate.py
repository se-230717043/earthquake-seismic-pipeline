# src/validate.py
import sqlite3
import os
import sys

DB_PATH = os.path.join("data", "earthquake.db")

def run_validations():
    conn = sqlite3.connect(DB_PATH)
    stop_failed = False

    # Check 1: Row count equality (STOP)
    raw_eq_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events").fetchone()[0]
    clean_eq_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events_clean").fetchone()[0]
    if raw_eq_cnt == clean_eq_cnt:
        print(f"PASS earthquake_events_clean row count equals raw ({clean_eq_cnt}={raw_eq_cnt})")
    else:
        print(f"STOP earthquake_events_clean row count mismatch ({clean_eq_cnt} != {raw_eq_cnt})")
        stop_failed = True

    # Check 2: No negative magnitude in cleaned column (STOP)
    neg_cnt = conn.execute("SELECT COUNT(*) FROM earthquake_events_clean WHERE magnitude < 0").fetchone()[0]
    if neg_cnt == 0:
        print("PASS no negative cleaned magnitude (0 negative)")
    else:
        print(f"STOP found {neg_cnt} negative magnitudes in cleaned layer")
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

    # Check 6: Check for unusual extreme events (WARN)
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