# src/clean_config.py
"""
Configuration thresholds and constants for M3 data cleaning pipeline.
"""

# Latitude and Longitude Valid Bounds
LAT_MIN = -90.0
LAT_MAX = 90.0
LON_MIN = -180.0
LON_MAX = 180.0

# Seismic Magnitude Thresholds
MAG_MIN_VALID = 0.0   # Seismic magnitudes cannot be negative
MAG_UNUSUAL_HIGH = 8.0 # Extreme seismic event threshold (kept, flagged)

# Elevation Sentinel Values
ELEVATION_SENTINEL = -999.0

# Data Quality Thresholds for Validation
MIN_USABLE_SHARE = 0.85 # At least 85% usable data per table