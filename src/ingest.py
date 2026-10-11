import os
import sys
import time
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=2.5&limit=100"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/elevation?latitude=38.42&longitude=27.14"

def get_utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def make_request_with_retry(url, max_retries=3, timeout=10):
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)

            if response.status_code in (401, 403):
                print(f"[ERROR] Auth failure ({response.status_code}) for {url}. Stopping.")
                sys.exit(1)

            if response.status_code in (429, 500, 502, 503, 504):
                print(f"[WARN] Status {response.status_code}. Retrying ({attempt}/{max_retries})...")
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"[WARN] Network error on attempt {attempt}: {e}")
            time.sleep(2 ** attempt)

    print(f"[ERROR] Failed to fetch {url} after {max_retries} attempts.")
    return None

def save_raw_response(source_name, data):
    timestamp = get_utc_timestamp()
    target_dir = os.path.join(RAW_DATA_DIR, source_name)
    os.makedirs(target_dir, exist_ok=True)

    filename = f"{timestamp}.json"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath

def main():
    print("=== Starting M1 Data Ingestion Pipeline ===")
    timestamp = get_utc_timestamp()
    summary = []

    # 1. Fetch USGS Data
    print("\nFetching USGS Earthquake data...")
    usgs_data = make_request_with_retry(USGS_URL)
    if usgs_data and "features" in usgs_data:
        record_count = len(usgs_data["features"])
        if record_count > 0:
            fp = save_raw_response("earthquake", usgs_data)
            summary.append(f"USGS: Successfully retrieved {record_count} records -> {fp}")
        else:
            print("[WARN] USGS returned empty feature list.")
            summary.append("USGS: Empty response received.")
    else:
        summary.append("USGS: Ingestion Failed.")

    # 2. Fetch Open-Meteo Data
    print("\nFetching Open-Meteo Elevation data...")
    meteo_data = make_request_with_retry(OPEN_METEO_URL)
    if meteo_data and "elevation" in meteo_data:
        fp = save_raw_response("elevation", meteo_data)
        summary.append(f"Open-Meteo: Successfully retrieved elevation metadata -> {fp}")
    else:
        summary.append("Open-Meteo: Ingestion Failed.")

    # Ingestion Summary Report
    print("\n================ Run Summary ================")
    print(f"Timestamp (UTC): {timestamp}")
    for item in summary:
        print(f"- {item}")
    print("=============================================\n")

if __name__ == "__main__":
    main()