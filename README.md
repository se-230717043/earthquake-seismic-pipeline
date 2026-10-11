# Earthquake & Seismic Activity Tracking Pipeline

## Project Goal & Research Question
This project focuses on ingesting, processing, and analyzing global seismic event data alongside elevation metadata to understand geographical patterns of seismic activity. The core research question addresses how earthquake magnitudes and frequency correlate with specific topographical elevations and regional fault locations.

## Primary & Secondary Data Sources
- **Primary Data Source:** [USGS Earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) (JSON format, minimum magnitude 2.5)
- **Secondary Data Source:** [Open-Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api) (Elevation metadata for geographical coordinates)

## Repository Structure
```text
earthquake-seismic-pipeline/
├── data/
│   └── raw/             # Raw JSON responses stored with UTC timestamps
├── docs/
│   └── sources.md       # Data source cards and API documentation
├── src/
│   └── ingest.py        # Python script for fetching and storing raw API data
├── .env.example         # Template for environment variables
├── .gitignore           # Git ignore rules for sensitive files and raw data
├── README.md            # Project overview and instructions
└── requirements.txt     # Required Python libraries