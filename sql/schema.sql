-- 1. Elevation Locations (Entity Table)
CREATE TABLE IF NOT EXISTS elevation_locations (
    location_key INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    elevation REAL,
    retrieved_at TEXT NOT NULL
) STRICT;

-- 2. Earthquake Events (Event Table)
CREATE TABLE IF NOT EXISTS earthquake_events (
    event_id TEXT NOT NULL,
    location_source_id TEXT NOT NULL,
    magnitude REAL NOT NULL,
    place TEXT,
    event_time TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    PRIMARY KEY (event_id, retrieved_at),
    FOREIGN KEY (location_source_id) REFERENCES elevation_locations(source_id)
) STRICT;

-- 3. Quarantine Table (For Invalid / Mismatched Records)
CREATE TABLE IF NOT EXISTS quarantine (
    quarantine_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    raw_record TEXT NOT NULL,
    reason TEXT NOT NULL,
    quarantined_at TEXT NOT NULL
) STRICT;