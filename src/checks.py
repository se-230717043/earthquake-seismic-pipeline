import os
import shutil
import sqlite3
import tempfile
from db import connect
from load import load_data

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "earthquake.db")

def check_duplicate_natural_key(con):
    try:
        con.execute("INSERT INTO elevation_locations (source_id, latitude, longitude, retrieved_at) VALUES ('loc_izmir_38.42_27.14', 38.42, 27.14, '2026-10-24T00:00:00Z');")
        return False
    except sqlite3.IntegrityError:
        return True

def check_orphan_event(con):
    try:
        con.execute("INSERT INTO earthquake_events (event_id, location_source_id, magnitude, event_time, retrieved_at) VALUES ('test_id', 'non_existent_loc', 5.0, '2026-10-24T00:00:00Z', '2026-10-24T00:00:00Z');")
        return False
    except sqlite3.IntegrityError:
        return True

def check_null_key(con):
    try:
        con.execute("INSERT INTO earthquake_events (event_id, location_source_id, magnitude, event_time, retrieved_at) VALUES (NULL, 'loc_izmir_38.42_27.14', 5.0, '2026-10-24T00:00:00Z', '2026-10-24T00:00:00Z');")
        return False
    except sqlite3.IntegrityError:
        return True

def check_wrong_type(con):
    try:
        con.execute("INSERT INTO earthquake_events (event_id, location_source_id, magnitude, event_time, retrieved_at) VALUES ('test_type', 'loc_izmir_38.42_27.14', 'INVALID_MAGNITUDE', '2026-10-24T00:00:00Z', '2026-10-24T00:00:00Z');")
        return False
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        return True

def get_row_counts(con):
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';").fetchall()]
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}

def run_checks():
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run load.py first.")
        return

    tmp_dir = tempfile.mkdtemp()
    try:
        temp_db = os.path.join(tmp_dir, "check.db")
        shutil.copyfile(DB_PATH, temp_db)
        
        # 1. Şema Kısıtlama Testleri
        con = connect(temp_db)
        dup_pass = check_duplicate_natural_key(con)
        orphan_pass = check_orphan_event(con)
        null_pass = check_null_key(con)
        type_pass = check_wrong_type(con)
        before_counts = get_row_counts(con)
        con.close()

        # 2. Idempotence Testi
        load_data(temp_db)
        
        con2 = connect(temp_db)
        after_counts = get_row_counts(con2)
        idempotence_pass = (before_counts == after_counts)

        # 3. Atomicity Testi
        before_atomic = get_row_counts(con2)
        try:
            with con2:
                con2.execute("INSERT INTO earthquake_events (event_id, location_source_id, magnitude, event_time, retrieved_at) VALUES ('bad_event', 'non_existent_loc', 5.0, '2026-10-24T00:00:00Z', '2026-10-24T00:00:00Z');")
        except sqlite3.IntegrityError:
            pass
        after_atomic = get_row_counts(con2)
        atomicity_pass = (before_atomic == after_atomic)
        con2.close()

        print("================ M2 Validation Checks ================")
        print(f"Duplicate natural key : {'PASS' if dup_pass else 'FAIL'}")
        print(f"Orphan event          : {'PASS' if orphan_pass else 'FAIL'}")
        print(f"NULL key              : {'PASS' if null_pass else 'FAIL'}")
        print(f"Wrong type            : {'PASS' if type_pass else 'FAIL'}")
        print(f"Idempotence           : {'PASS' if idempotence_pass else 'FAIL'}")
        print(f"Atomicity             : {'PASS' if atomicity_pass else 'FAIL'}")
        print("======================================================")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_checks()