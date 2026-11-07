-- sql/clean_schema.sql
-- M3 Cleaned Layer Tables with STRICT mode

CREATE TABLE IF NOT EXISTS elevation_locations_clean (
    location_key INTEGER NOT NULL PRIMARY KEY,
    source_id_raw TEXT,
    source_id TEXT,
    source_id_flag TEXT NOT NULL CHECK (source_id_flag IN ('ok', 'missing_not_reported', 'standardized', 'invalid')),
    latitude_raw REAL,
    latitude REAL,
    longitude_raw REAL,
    longitude REAL,
    coordinate_flag TEXT NOT NULL CHECK (coordinate_flag IN ('ok', 'missing_not_reported', 'invalid_out_of_bounds')),
    elevation_raw REAL,
    elevation REAL,
    elevation_flag TEXT NOT NULL CHECK (elevation_flag IN ('ok', 'missing_not_reported', 'invalid_sentinel', 'unusual_extreme')),
    retrieved_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS earthquake_events_clean (
    event_id TEXT NOT NULL PRIMARY KEY,
    location_source_id_raw TEXT,
    location_source_id TEXT,
    location_source_id_flag TEXT NOT NULL CHECK (location_source_id_flag IN ('ok', 'missing_not_reported', 'unresolved_fk')),
    magnitude_raw REAL,
    magnitude REAL,
    magnitude_flag TEXT NOT NULL CHECK (magnitude_flag IN ('ok', 'missing_not_reported', 'invalid_negative', 'unusual_high')),
    place_raw TEXT,
    place TEXT,
    place_flag TEXT NOT NULL CHECK (place_flag IN ('ok', 'missing_not_reported', 'standardized_text')),
    event_time TEXT NOT NULL,
    retrieved_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS quarantine_clean (
    quarantine_id INTEGER NOT NULL PRIMARY KEY,
    source_name TEXT NOT NULL,
    raw_record TEXT NOT NULL,
    reason TEXT NOT NULL,
    quarantined_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS location_mapping (
    alias TEXT NOT NULL PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    note TEXT NOT NULL
) STRICT;