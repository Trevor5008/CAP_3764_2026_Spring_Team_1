"""
FDOT Work Program Data Ingestion Module

This module fetches, validates, and cleans FDOT Work Program data
from the Florida Department of Transportation (FDOT) ArcGIS REST API.

Each supported layer is written to its own GeoPackage file under
`src/data/processed/` so that analysis can treat them as separate inputs.
"""

import requests
from pathlib import Path
import geopandas as gpd

BASE = "https://gis.fdot.gov/arcgis/rest/services/Work_Program_Current/FeatureServer/"

ADMINISTRATIVE_LAYER = "0"
CONSTRUCTION_LAYER = "2" # Most comprehensive layer
MAINTENANCE_OF_TRAFFIC_LAYER = "11"
PLANNING_LAYER = "14"


def fetch_layer(layer_id: str, page_size: int = 2000, where: str = "1=1") -> gpd.GeoDataFrame:
    """
    Fetch all features for a single FDOT Work Program layer using pagination.

    Parameters
    ----------
    layer_id : str
        Layer index on the Work_Program_Current FeatureServer (e.g. \"2\" for construction).
    page_size : int, optional
        Number of records per API request. Default: 2000.
    where : str, optional
        SQL WHERE clause for filtering records. Default: \"1=1\" (all records).
        Examples:
        - \"CONTYNAM = 'MIAMI-DADE'\" (Miami-Dade County only)
        - \"CONTYNAM IN ('MIAMI-DADE', 'BROWARD')\" (Multiple counties)

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing all matching features with CRS EPSG:4326.
    """
    features = []
    offset = 0

    while True:
        params = {
            "where": where,
            "outFields": "*",
            "f": "geojson",
            "outSR": 4326,
            "resultRecordCount": page_size,
            "resultOffset": offset,
        }

        url = f"{BASE}{layer_id}/query"
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()

        batch = data.get("features", [])
        if not batch:
            break

        features.extend(batch)
        offset += len(batch)

        # stop if server returns fewer than requested (last page)
        if len(batch) < page_size:
            break

    return gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

# Only ingest Miami-Dade County construction data
def ingest_construction(where: str = "CONTYNAM = 'MIAMI-DADE'") -> None:
    """
    Ingest the construction layer (layer 2) and persist a cleaned GeoPackage.

    Cleaning rules:
    - Keep only rows with non-empty geometries
    - Keep only rows with LOC_ERROR == \"NO ERROR\"
    """
    print("Fetching construction layer...")
    gdf = fetch_layer(CONSTRUCTION_LAYER, where=where)

    print("Cleaning construction data...")
    gdf = gdf[
        (~gdf.geometry.is_empty) &
        (gdf["LOC_ERROR"] == "NO ERROR")
    ].copy()

    print(f"\nConstruction data shape: {gdf.shape}")
    print(f"Empty geometries: {gdf.geometry.is_empty.sum()}")
    print(f"Null geometries: {gdf.geometry.isna().sum()}")
    print(f"\nLocation error breakdown:\n{gdf['LOC_ERROR'].value_counts(dropna=False).head(10)}")

    out_path = Path("data/processed/fdot_work_program_construction.gpkg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    print(f"\nConstruction data saved to: {out_path}")


def ingest_administrative(where: str = "CONTYNAM = 'MIAMI-DADE'") -> None:
    """
    Ingest the administrative layer (layer 0) and persist a GeoPackage.
    """
    print("Fetching administrative layer...")
    gdf = fetch_layer(ADMINISTRATIVE_LAYER, where=where)

    print(f"Administrative data shape: {gdf.shape}")
    out_path = Path("data/processed/fdot_work_program_admin.gpkg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    print(f"Administrative data saved to: {out_path}")


def ingest_maintenance_of_traffic(where: str = "CONTYNAM = 'MIAMI-DADE'") -> None:
    """
    Ingest the maintenance-of-traffic layer (layer 11) and persist a GeoPackage.
    """
    print("Fetching maintenance of traffic layer...")
    gdf = fetch_layer(MAINTENANCE_OF_TRAFFIC_LAYER, where=where)

    print(f"Maintenance of traffic data shape: {gdf.shape}")
    out_path = Path("data/processed/fdot_work_program_mot.gpkg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    print(f"Maintenance of traffic data saved to: {out_path}")


def ingest_planning(where: str = "CONTYNAM = 'MIAMI-DADE'") -> None:
    """
    Ingest the planning layer (layer 14) and persist a GeoPackage.
    """
    print("Fetching planning layer...")
    gdf = fetch_layer(PLANNING_LAYER, where=where)

    print(f"Planning data shape: {gdf.shape}")
    out_path = Path("data/processed/fdot_work_program_planning.gpkg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GPKG")
    print(f"Planning data saved to: {out_path}")


if __name__ == "__main__":
    # Ingest each layer as a separate GeoPackage for downstream analysis.
    ingest_construction()
    ingest_administrative()
    ingest_maintenance_of_traffic()
    ingest_planning()
