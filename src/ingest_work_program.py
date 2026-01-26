import requests
from pathlib import Path
import geopandas as gpd

BASE = "https://gis.fdot.gov/arcgis/rest/services/Work_Program_Current/FeatureServer/2/query"

def fetch_all(page_size=2000, where="1=1"):
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

gdf_mdc = fetch_all(where="CONTYNAM = 'MIAMI-DADE'")

# Drop bad data before saving
gdf_mdc = gdf_mdc[
    (~gdf_mdc.geometry.is_empty) &
    (gdf_mdc["LOC_ERROR"] == "NO ERROR")
].copy()

print(gdf_mdc.shape)

# Basic Validation
print("rows:", len(gdf_mdc))
print("empty geometries:", gdf_mdc.geometry.is_empty.sum())
print("null geometries:", gdf_mdc.geometry.isna().sum())
print("loc_error breakdown:\n", gdf_mdc["LOC_ERROR"].value_counts(dropna=False).head(10))

# Data Persistence -> data/processed
out_path = Path("data/processed/fdot_work_program_construction.gpkg")
out_path.parent.mkdir(parents=True, exist_ok=True)
gdf_mdc.to_file(out_path, driver="GPKG")
gdf_mdc.head(1).T
