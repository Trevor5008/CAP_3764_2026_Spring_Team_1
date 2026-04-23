"""Load and merge construction GeoPackage + risk-proxy CSV for the Streamlit map."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st

from app_data.app_constants import GPKG_PATH, RISK_CSV_PATH
from app_data.features import wpp_haz_tp_to_desc


@st.cache_data(show_spinner="Loading Miami-Dade construction segments…")
def load_construction_gdf() -> gpd.GeoDataFrame:
    """GeoPackage rows merged with risk-proxy CSV so tooltips have risk_proxy, Normalized_Length, etc."""
    gdf = gpd.read_file(GPKG_PATH)
    gdf["CONTYNAM"] = gdf["CONTYNAM"].astype(str).str.strip()
    if "WPWKMIXN" in gdf.columns:
        gdf["WPWKMIXN"] = gdf["WPWKMIXN"].astype(str).str.strip()
    if "WPPHAZTP" in gdf.columns:
        gdf["WPPHAZTP"] = gdf["WPPHAZTP"].astype(str).str.strip().str.upper()
    gdf = gdf[gdf["CONTYNAM"] == "MIAMI-DADE"].copy()

    if RISK_CSV_PATH.is_file():
        extra = pd.read_csv(
            RISK_CSV_PATH,
            usecols=["OBJECTID", "WPPHAZTP_DESC", "risk_proxy", "Normalized_Length", "PHASE_WEIGHT"],
        )
        gdf = gdf.merge(extra, on="OBJECTID", how="left")

    if "WPPHAZTP_DESC" not in gdf.columns:
        gdf["WPPHAZTP_DESC"] = np.nan
    miss = gdf["WPPHAZTP_DESC"].isna() | (gdf["WPPHAZTP_DESC"].astype(str).str.strip() == "")
    if miss.any():
        gdf.loc[miss, "WPPHAZTP_DESC"] = gdf.loc[miss, "WPPHAZTP"].map(wpp_haz_tp_to_desc)

    return gdf
