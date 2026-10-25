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
---

## Milestone 2: Data Storage & Schema Design

### Database Architecture
The database is built using SQLite with `STRICT` table mode enabled to enforce explicit data typing. Primary keys, foreign keys, and unique constraints are strictly configured.

### Entity-Relationship (ER) Diagram
```mermaid
erDiagram
    elevation_locations ||--o{ earthquake_events : "has"
    elevation_locations {
        int location_key PK
        text source_id UK
        real latitude
        real longitude
        real elevation
        text retrieved_at
    }
    earthquake_events {
        text event_id PK
        text location_source_id FK
        real magnitude
        text place
        text event_time
        text retrieved_at PK
    }
    quarantine {
        int quarantine_id PK
        text source_name
        text raw_record
        text reason
        text quarantined_at
    }