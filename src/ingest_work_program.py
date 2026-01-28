"""
FDOT Work Program Construction Data Ingestion Module

This module fetches, validates, and cleans construction work program data
from the Florida Department of Transportation (FDOT) ArcGIS REST API.
"""

import requests
from pathlib import Path
import geopandas as gpd

BASE = "https://gis.fdot.gov/arcgis/rest/services/Work_Program_Current/FeatureServer/2/query"


def fetch_all(page_size=2000, where="1=1"):
    """
    Fetches all features from FDOT ArcGIS FeatureServer using pagination.
    
    This function implements automatic pagination to handle large datasets
    that exceed the API's single-request limit. It continues fetching
    until all matching records are retrieved.
    
    Parameters
    ----------
    page_size : int, optional
        Number of records per API request. Default: 2000.
        Larger values reduce API calls but increase memory usage per request.
    where : str, optional
        SQL WHERE clause for filtering records. Default: "1=1" (all records).
        Examples:
        - "CONTYNAM = 'MIAMI-DADE'" (Miami-Dade County only)
        - "CONTYNAM IN ('MIAMI-DADE', 'BROWARD')" (Multiple counties)
    
    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame containing all matching features with CRS EPSG:4326.
        Includes all attribute fields from the source FeatureServer.
    
    Raises
    ------
    requests.HTTPError
        If the API request fails (non-2xx status code).
    requests.Timeout
        If the API request exceeds the 60-second timeout.
    
    Examples
    --------
    >>> # Fetch all Miami-Dade County records
    >>> gdf = fetch_all(where="CONTYNAM = 'MIAMI-DADE'")
    >>> 
    >>> # Fetch with custom page size
    >>> gdf = fetch_all(page_size=1000, where="CONTYNAM = 'BROWARD'")
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

        r = requests.get(BASE, params=params, timeout=60)
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


# Main execution block
if __name__ == "__main__":
    # Step 1: Fetch Miami-Dade County construction work program data
    print("Fetching data from FDOT ArcGIS API...")
    gdf_mdc = fetch_all(where="CONTYNAM = 'MIAMI-DADE'")
    
    # Step 2: Data cleaning - filter invalid records
    # Remove rows with empty geometries and location errors
    print("Cleaning data...")
    gdf_mdc = gdf_mdc[
        (~gdf_mdc.geometry.is_empty) &
        (gdf_mdc["LOC_ERROR"] == "NO ERROR")
    ].copy()
    
    # Step 3: Validation reporting
    print(f"\nData shape: {gdf_mdc.shape}")
    print(f"Total rows: {len(gdf_mdc)}")
    print(f"Empty geometries: {gdf_mdc.geometry.is_empty.sum()}")
    print(f"Null geometries: {gdf_mdc.geometry.isna().sum()}")
    print(f"\nLocation error breakdown:\n{gdf_mdc['LOC_ERROR'].value_counts(dropna=False).head(10)}")
    
    # Step 4: Persist cleaned data to GeoPackage
    out_path = Path("data/processed/fdot_work_program_construction.gpkg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf_mdc.to_file(out_path, driver="GPKG")
    print(f"\nData saved to: {out_path}")
    
    # Display sample record
    print("\nSample record:")
    print(gdf_mdc.head(1).T)
