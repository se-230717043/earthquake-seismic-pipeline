# Data Source Cards

---

## Primary Data Source: USGS Earthquake Hazards Program API

- **Source Name:** USGS Earthquake API
- **Provider / Host:** United States Geological Survey (USGS)
- **URL / Endpoint:** `https://earthquake.usgs.gov/fdsnws/event/1/query`
- **Access / Auth Requirements:** Publicly available API. No authentication or API key required.
- **Data Format:** GeoJSON / JSON
- **Ingestion Method:** Automated HTTP GET requests via `src/ingest.py`
- **License / Terms:** Public Domain (USGS Data Policy)
- **Update Frequency:** Real-time / Every 15 minutes
- **Entity Description:** Each feature represents a single seismic event (earthquake) containing geographical coordinates (latitude, longitude, depth), magnitude, place description, and UTC epoch timestamp.
- **Known Limitations / Issues:** Rate limits apply under heavy loads; high depth values might require special handling during preprocessing.

---

## Secondary Data Source: Open-Meteo Elevation API

- **Source Name:** Open-Meteo Elevation API
- **Provider / Host:** Open-Meteo
- **URL / Endpoint:** `https://api.open-meteo.com/v1/elevation`
- **Access / Auth Requirements:** Publicly available API. Free tier does not require an API key for reasonable request volumes.
- **Data Format:** JSON
- **Ingestion Method:** Automated HTTP GET requests via `src/ingest.py`
- **License / Terms:** Non-commercial free tier / Creative Commons Attribution 4.0 International
- **Update Frequency:** Static topographical elevation mapping based on DEM datasets.
- **Entity Description:** Maps input latitude and longitude coordinates to precise surface elevation above sea level in meters.
- **Known Limitations / Issues:** Resolution is tied to 90m/30m digital elevation models; oceanic coordinates return 0 or null elevation values.

---

## Recovered M4 Snapshot Provenance

- **Retrieval time:** 2026-11-15 16:16:20 UTC.
- **USGS endpoint:** `https://earthquake.usgs.gov/fdsnws/event/1/query`.
- **USGS parameters:** `format=geojson`, `minmagnitude=2.5`, `limit=1500`, `orderby=time`.
- **USGS result:** 1,500 real event records; 1,500 distinct event IDs.
- **Event period:** 2026-10-22 08:34:19 through 2026-11-15 15:52:42 UTC.
- **Geographical scope:** Global; observed coordinates span latitude -62.4457 to 86.7236 and longitude -179.9938 to 179.9661.
- **Open-Meteo endpoint:** `https://api.open-meteo.com/v1/elevation`.
- **Open-Meteo result:** 1,499 elevations for 1,499 unique event coordinates; two genuine events share a coordinate. Requests used 100-coordinate paced batches with rate-limit backoff.
- **Raw preservation:** both source payloads, parameters, and raw elevation responses are stored under `data/raw/` with the shared UTC timestamp `20261115T161620Z`.
- **Scope extension:** M0/M1 had no fixed dates. The global geography and M2.5 threshold were preserved, while the moving API limit was explicitly extended from 100 to 1,500 to satisfy M4's minimum record count.
- **Historical difference:** the M3 report referenced 200 events, but neither those raw snapshots nor their database were present, so that exact moving-window set cannot be reproduced.
