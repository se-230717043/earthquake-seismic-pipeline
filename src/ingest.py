"""Fetch a reproducible raw USGS snapshot and coordinate-matched elevations."""

import json
import os
import sys
import time
import argparse
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# M4 expands the moving snapshot from the original latest 100 to latest 1,500
# events. The global geography and M2.5 threshold are unchanged; because M0/M1
# encoded no fixed dates, the larger limit necessarily extends the look-back.
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_PARAMS = {"format": "geojson", "minmagnitude": 2.5, "limit": 1500, "orderby": "time"}
OPEN_METEO_URL = "https://api.open-meteo.com/v1/elevation"
ELEVATION_BATCH_SIZE = 100
ELEVATION_BATCH_PAUSE_SECONDS = 2.0


def get_utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_request_with_retry(url, params=None, max_retries=8, timeout=30):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code in (401, 403):
                print(f"[ERROR] Auth failure ({response.status_code}) for {url}. Stopping.")
                sys.exit(1)
            if response.status_code in (429, 500, 502, 503, 504):
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(60, 5 * (2 ** (attempt - 1)))
                print(f"[WARN] Status {response.status_code}. Retrying in {delay:.0f}s ({attempt}/{max_retries})...")
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            print(f"[WARN] Network error on attempt {attempt}: {exc}")
            time.sleep(2 ** attempt)
    print(f"[ERROR] Failed to fetch {url} after {max_retries} attempts.")
    return None


def save_raw_response(source_name, data, timestamp):
    target_dir = os.path.join(RAW_DATA_DIR, source_name)
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, f"{timestamp}.json")
    with open(filepath, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    return filepath


def event_coordinates(usgs_data):
    """Extract valid unique (latitude, longitude) pairs in event order."""
    coordinates = []
    seen = set()
    for feature in usgs_data.get("features", []):
        values = (feature.get("geometry") or {}).get("coordinates") or []
        if len(values) < 2:
            continue
        longitude, latitude = values[:2]
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        key = (round(float(latitude), 5), round(float(longitude), 5))
        if key not in seen:
            seen.add(key)
            coordinates.append(key)
    return coordinates


def fetch_elevations(coordinates):
    """Fetch Open-Meteo elevation for each event coordinate in bounded batches."""
    locations = []
    raw_responses = []
    request_batches = []
    for start in range(0, len(coordinates), ELEVATION_BATCH_SIZE):
        batch = coordinates[start:start + ELEVATION_BATCH_SIZE]
        params = {
            "latitude": ",".join(str(lat) for lat, _ in batch),
            "longitude": ",".join(str(lon) for _, lon in batch),
        }
        response = make_request_with_retry(OPEN_METEO_URL, params=params)
        if response is None:
            raise RuntimeError(f"Open-Meteo failed for coordinate batch beginning at {start}")
        elevations = response.get("elevation")
        if not isinstance(elevations, list) or len(elevations) != len(batch):
            raise ValueError("Open-Meteo elevation response did not match requested coordinates")
        request_batches.append(params)
        raw_responses.append(response)
        locations.extend(
            {"latitude": lat, "longitude": lon, "elevation": elevation}
            for (lat, lon), elevation in zip(batch, elevations)
        )
        if start + ELEVATION_BATCH_SIZE < len(coordinates):
            time.sleep(ELEVATION_BATCH_PAUSE_SECONDS)
    return {
        "source": "Open-Meteo Elevation API",
        "endpoint": OPEN_METEO_URL,
        "request_batches": request_batches,
        "locations": locations,
        "raw_responses": raw_responses,
    }


def main(usgs_path=None):
    print("=== Starting data ingestion pipeline ===")
    timestamp = get_utc_timestamp()
    summary = []

    if usgs_path:
        usgs_path = os.path.abspath(usgs_path)
        print(f"\nReusing preserved USGS raw payload: {usgs_path}")
        with open(usgs_path, "r", encoding="utf-8") as handle:
            usgs_data = json.load(handle)
        timestamp = os.path.basename(usgs_path).replace(".json", "")
    else:
        print("\nFetching USGS earthquake data...")
        usgs_data = make_request_with_retry(USGS_URL, params=USGS_PARAMS)
    if usgs_data and usgs_data.get("features"):
        if usgs_path:
            summary.append(f"USGS: reused {len(usgs_data['features'])} preserved records -> {usgs_path}")
        else:
            usgs_data["pipeline_metadata"] = {
                "endpoint": USGS_URL,
                "parameters": USGS_PARAMS,
                "retrieved_at_utc": timestamp,
            }
            filepath = save_raw_response("earthquake", usgs_data, timestamp)
            summary.append(f"USGS: {len(usgs_data['features'])} records -> {filepath}")

        print("\nFetching Open-Meteo elevation data for event coordinates...")
        coordinates = event_coordinates(usgs_data)
        meteo_data = fetch_elevations(coordinates)
        meteo_data["retrieved_at_utc"] = timestamp
        filepath = save_raw_response("elevation", meteo_data, timestamp)
        summary.append(f"Open-Meteo: {len(coordinates)} coordinate elevations -> {filepath}")
    else:
        summary.append("USGS: ingestion failed or returned no records.")
        summary.append("Open-Meteo: skipped because USGS ingestion failed.")

    print("\n================ Run Summary ================")
    print(f"Timestamp (UTC): {timestamp}")
    for item in summary:
        print(f"- {item}")
    print("=============================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--elevations-from",
        help="Reuse a preserved USGS raw JSON and fetch only matching elevations.",
    )
    args = parser.parse_args()
    main(args.elevations_from)
