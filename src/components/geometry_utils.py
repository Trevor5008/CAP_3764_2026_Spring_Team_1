"""Pure geometry helpers for map layers (no I/O, no Streamlit)."""

# Helper function to convert a geometry to a list of longitude and latitude points
def geom_to_lonlat_path(geom) -> list[list[float]] | None:
    """Single PathLayer path as [[lon, lat], ...]."""
    if geom is None or geom.is_empty:
        return None
    gt = geom.geom_type
    if gt == "LineString":
        return [[float(lon), float(lat)] for lon, lat in geom.coords]
    if gt == "MultiLineString":
        longest = max(geom.geoms, key=lambda g: g.length)
        return [[float(lon), float(lat)] for lon, lat in longest.coords]
    return None
