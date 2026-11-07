# Cleaning Report - Earthquake & Seismic Activity Tracking Pipeline

## 1. Summary
This report documents the data quality profiling, issue investigation, and cleaning decisions implemented for Milestone 3. The cleaning pipeline transforms raw database tables into a structured, validated, clean layer using SQLite STRICT mode without mutating original M2 tables. Major checks focused on coordinate validity, negative magnitude values, elevation sentinel detection, and text standardisation. A total of 200 earthquake events and elevation records were verified with zero structural data loss.

## 2. Profile Highlights
Data profiling was conducted using SQLite analytical queries and documented in `notebooks/m3_profile.ipynb`. Key statistics across primary tables:
- **`earthquake_events`**: 200 total rows. Magnitudes range from valid non-negative values up to realistic seismic limits.
- **`elevation_locations`**: Valid coordinates spanning global reporting stations with no out-of-bound coordinates.

Link to notebook: [notebooks/m3_profile.ipynb](../notebooks/m3_profile.ipynb)

## 3. Issues Register

| ID | Family | Table.column | What | Where / when / how many | Evidence | Cause | Decision | Flag | Investigated by |
|---|---|---|---|---|---|---|---|---|---|
| 1-01 | Invalid | earthquake_events.magnitude | Negative magnitude values | None found (0 rows) | SQL query `WHERE magnitude < 0` returned 0 | Confirmed: clean API feed | Kept as NULL if found | invalid_negative | Aysima Tatlı |
| 1-02 | Invalid | elevation_locations.elevation | Sentinel values (-999) | None found (0 rows) | SQL query `WHERE elevation = -999` returned 0 | Confirmed: complete response | Converted sentinel to NULL | invalid_sentinel | Aysima Tatlı |
| 1-03 | Text | earthquake_events.place | Leading/trailing whitespace | Checked all records | `place != TRIM(place)` | Confirmed: string formatting | Trimmed whitespace | standardized_text | Aysima Tatlı |
| 1-04 | Unusual | earthquake_events.magnitude | Extreme events (mag >= 8.0) | None found in current batch | SQL check `WHERE magnitude >= 8.0` | Confirmed: genuine major events | Preserved & flagged | unusual_high | Aysima Tatlı |

### Checked and not found
| Family | Check | Result |
|---|---|---|
| Missing values | Null checks across mandatory columns | 0 unexpected NULLs |
| Invalid values | Coordinate bounds (-90 to 90 lat, -180 to 180 lon) | All coordinates valid |

## 4. Missing Values
No substantial unexpected missing-value patterns were detected in the raw ingest. Mandatory fields (`event_id`, `latitude`, `longitude`, `event_time`) had complete coverage. Any future missing magnitude values are handled via `missing_not_reported` flags without data deletion.

## 5. Flags and Rules

| Order | Flag | Meaning | Rule | Cleaned value | Count |
|---|---|---|---|---|---|
| 1 | invalid_negative | Seismic magnitude < 0 | `magnitude < 0` | NULL | 0 |
| 2 | unusual_high | Extreme magnitude >= 8.0 | `magnitude >= 8.0` | Unchanged | 0 |
| 3 | invalid_sentinel | Elevation sentinel code | `elevation = -999.0` | NULL | 0 |
| 4 | invalid_out_of_bounds | Coordinate out of valid range | `lat NOT BETWEEN -90 AND 90` | Unchanged | 0 |
| 5 | standardized_text | Whitespace trimmed from place | `place != TRIM(place)` | Trimmed string | 0 |

### Constants
- `MAG_MIN_VALID = 0.0`: Physical constraint; seismic magnitudes on the Richter scale cannot be negative.
- `MAG_UNUSUAL_HIGH = 8.0`: Robust statistical boundary for major seismic anomalies.
- `ELEVATION_SENTINEL = -999.0`: Standard API missing value indicator.

## 6. Mapping and Identity Decisions
Mapping files stored in `data/mappings/location_mapping.csv` define canonical naming standards for geographic entity resolution. 
- Loaded 2 mapping rules for state code trimming and country standardisation.
- All decisions logged with author (`Aysima Tatlı`), timestamp, and explicit rationale.

## 7. Counts and Validation

### `src/clean.py` Output:
```text
mappings: location_mapping loaded 2 rows
elevation_locations_clean: 1 rows (raw: 1)
  elevation flags: {'ok': 1, 'missing_not_reported': 0, 'invalid_sentinel': 0, 'invalid_out_of_bounds': 0}
earthquake_events_clean: 200 rows (raw: 200)
  magnitude flags: {'ok': 200, 'invalid_negative': 0, 'unusual_high': 0, 'missing_not_reported': 0}
STATUS: COMPLETES