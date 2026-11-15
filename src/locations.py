"""Deterministic location identities shared by ingestion, loading, and tests."""

COORDINATE_DECIMALS = 5


def source_id_for_coordinates(latitude, longitude):
    """Return a stable ID at roughly metre-scale coordinate precision."""
    lat = round(float(latitude), COORDINATE_DECIMALS)
    lon = round(float(longitude), COORDINATE_DECIMALS)
    return f"loc_{lat:+.{COORDINATE_DECIMALS}f}_{lon:+.{COORDINATE_DECIMALS}f}"
