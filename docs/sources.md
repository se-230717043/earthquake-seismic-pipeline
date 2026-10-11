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
-