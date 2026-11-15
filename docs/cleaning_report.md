# Cleaning Report - Earthquake & Seismic Activity Tracking Pipeline

## 1. Summary

The M3 clean layer is non-destructive: raw M2 tables remain intact, while cleaned tables retain raw values, cleaned values, and explicit flags. For the corrected M4 snapshot, 1,500 USGS events and 1,499 coordinate-specific Open-Meteo elevations were loaded. The clean layer contains 1,500 unique events; two genuine events share one coordinate, and no critical record was quarantined.

## 2. M4 correction to the M3 pipeline

Exploration confirmed a serious prior defect: `src/load.py` assigned every earthquake to `loc_izmir_38.42_27.14`, regardless of the event geometry. This made the earlier one-location elevation analysis invalid. The correction:

- derives a deterministic source ID from each event latitude/longitude at five decimal places;
- retains each USGS event's actual coordinates;
- requests Open-Meteo elevation for every unique event coordinate in bounded batches;
- stores source endpoint, parameters, retrieval timestamp, and raw responses;
- upserts locations and events idempotently;
- deduplicates repeated retrieval snapshots by event ID in the clean layer, keeping the latest;
- validates that coordinate IDs and coordinate pairs have a one-to-one count; and
- adds `tests/test_location_mapping.py` as a regression test.

## 3. Profile highlights

| Measure | Result |
|---|---:|
| Raw event snapshots | 1,500 |
| Distinct raw event IDs | 1,500 |
| Clean unique events | 1,500 |
| Coordinate-specific locations | 1,499 |
| Quarantined records | 0 |
| Magnitude range | 2.5-7.0 |
| Elevation range | -32-5,835 m |

## 4. Issues register

| ID | Family | Table/column | What | Count | Decision | Flag | Investigated by |
|---|---|---|---:|---:|---|---|---|
| 1-01 | Scope | earthquake_events.magnitude | Below the project's M2.5 collection threshold | 0 | Convert to NULL if encountered; negative magnitudes are not inherently unphysical | outside_scope | Aysima Tatlı |
| 1-02 | Invalid | elevation_locations.elevation | Sentinel -999 | 0 | Convert to NULL if encountered | invalid_sentinel | Aysima Tatlı |
| 1-03 | Text | earthquake_events.place | Surrounding whitespace | 0 | Trim while retaining raw value | standardized_text | Aysima Tatlı |
| 1-04 | Unusual | earthquake_events.magnitude | Magnitude >=8.0 | 0 | Retain valid event and flag | unusual_high | Aysima Tatlı |
| 1-05 | Identity | earthquake_events.location_source_id | All events mapped to İzmir | Prior pipeline affected all rows | Replace with coordinate-derived ID and matched elevation; regression test | corrected in loader | M4 assisted review; team confirmation required |
| 1-06 | Duplicate | earthquake_events.event_id | Event can recur in multiple retrieval snapshots | 0 in current snapshot | Latest snapshot retained in clean layer | deduplicated by event ID | M4 assisted review; team confirmation required |

## 5. Flag results and validation

All 1,500 cleaned magnitudes are `ok`; all 1,499 elevation and coordinate flags are `ok`. The inclusive reporting filter `ok + unusual_high` is used because unusual high values are scientifically valid. Validation passes for distinct-event counts, the M2.5 collection threshold, foreign keys, usable share, coordinate bounds, coordinate-specific mapping, and unusual-event reporting. M2 constraint, idempotence, and atomicity checks also pass.

## 6. Provenance

The corrected data were retrieved at **2026-11-15 16:16:20 UTC**. Geography remains global and the threshold remains M2.5. Because the original M1 request encoded no fixed start/end dates, meeting the M4 minimum required an explicit extension from `limit=100` to `limit=1500`, ordered by time; the resulting event period is 2026-10-22 08:34:19 through 2026-11-15 15:52:42 UTC. Open-Meteo returned elevations for all 1,499 unique coordinates in paced batches with retry/backoff. The historical 200-row M3 dataset remains unrecoverable because its moving-window raw files were absent.
