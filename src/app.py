"""
Streamlit demo: risk-proxy prediction + optional map of FDOT segments (Miami-Dade).

Run from `src/`: streamlit run app.py
API: from `src/`: uvicorn main:app --reload
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from shapely.geometry import mapping
from shapely.ops import unary_union

from features import WORK_MIX_TOP12_LABELS, reduce_work_mix, wpp_haz_tp_to_desc

API_BASE = "http://127.0.0.1:8000"

_DATA_PATH = Path(__file__).resolve().parent / "data/processed/fdot_work_program_construction.gpkg"
_CSV_RISK_PATH = Path(__file__).resolve().parent / "data/processed/construction_with_risk_proxy.csv"

# Sentinel: any WPWKMIXN not in top-12 buckets to "Other" in the model
_OTHER_SENTINEL = "__OTHER_BUCKET__"

# legend for phase codes
PHASE_CHOICES: dict[str, str] = {
    "4": "Contract Executed (code 4)",
    "8": "Pre-Construction (code 8)",
    "A": "Construction Completed (code A)",
    "2": "Active Construction (code 2)",
    "3": "Active Construction (code 3)",
    "6": "Active Construction (code 6)",
    "7": "Active Construction (code 7)",
}


@st.cache_data(show_spinner="Loading Miami-Dade construction segments…")
def load_construction_gdf() -> tuple[gpd.GeoDataFrame, dict]:
    """GeoPackage rows + optional CSV merge for WPPHAZTP_DESC, risk_proxy, etc."""
    gdf = gpd.read_file(_DATA_PATH)
    gdf["CONTYNAM"] = gdf["CONTYNAM"].astype(str).str.strip()
    gdf["WPWKMIXN"] = gdf["WPWKMIXN"].astype(str).str.strip()
    gdf["WPPHAZTP"] = gdf["WPPHAZTP"].astype(str).str.strip().str.upper()
    gdf = gdf[gdf["CONTYNAM"] == "MIAMI-DADE"].copy()
    if _CSV_RISK_PATH.is_file():
        extra = pd.read_csv(
            _CSV_RISK_PATH,
            usecols=["OBJECTID", "WPPHAZTP_DESC", "risk_proxy", "Normalized_Length", "PHASE_WEIGHT"],
        )
        gdf = gdf.merge(extra, on="OBJECTID", how="left")
    if "WPPHAZTP_DESC" not in gdf.columns:
        gdf["WPPHAZTP_DESC"] = np.nan
    missing = gdf["WPPHAZTP_DESC"].isna() | (gdf["WPPHAZTP_DESC"].astype(str).str.len() == 0)
    gdf.loc[missing, "WPPHAZTP_DESC"] = gdf.loc[missing, "WPPHAZTP"].map(
        lambda c: wpp_haz_tp_to_desc(str(c)) if c is not None else None
    )
    merged = unary_union(gdf.geometry.tolist())
    hull = merged.convex_hull
    outline = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Study area (segment coverage)"},
                "geometry": mapping(hull),
            }
        ],
    }
    return gdf, outline


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


def work_mix_for_api(ui_value: str) -> str:
    if ui_value == _OTHER_SENTINEL:
        return "UNLISTED_WORK_MIX"
    return ui_value


def reduced_bucket_for_filter(ui_value: str) -> str:
    if ui_value == _OTHER_SENTINEL:
        return "Other"
    return reduce_work_mix(ui_value)


def _format_tooltip_float(value, nd: int = 4) -> str:
    if value is None or (isinstance(value, (float, np.floating)) and (np.isnan(value) or np.isinf(value))):
        return "—"
    if isinstance(value, (int, float, np.integer, np.floating)) and pd.isna(value):
        return "—"
    try:
        return f"{float(value):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


st.title("CAP 3764 — FDOT risk proxy visualizer")
st.caption(
    "Miami-Dade Work Program construction segments (EPSG:4326). This is a visualizer for the risk proxy model. "
    "Map segments stay hidden until you turn them on. "
    "The map displays the segments that match the criteria above."
)

gdf_all, study_area_geojson = load_construction_gdf()

col_left, col_right = st.columns((1, 1.2), gap="large")

with col_left:
    st.subheader("Inputs")
    fiscal_year = st.number_input("Fiscal year", min_value=2023, max_value=2030, value=2026, step=1)
    phase_code = st.selectbox(
        "Construction phase (WPPHAZTP)",
        options=list(PHASE_CHOICES.keys()),
        format_func=lambda c: PHASE_CHOICES[c],
        index=0,
    )
    work_options = list(WORK_MIX_TOP12_LABELS) + [_OTHER_SENTINEL]
    work_mix_ui = st.selectbox(
        "Work mix (WPWKMIXN, training top-12 + Other)",
        options=work_options,
        format_func=lambda x: "Other (anything outside top-12)" if x == _OTHER_SENTINEL else x,
        index=list(WORK_MIX_TOP12_LABELS).index("RESURFACING") if "RESURFACING" in WORK_MIX_TOP12_LABELS else 0,
    )
    work_mix_api = work_mix_for_api(work_mix_ui)

    if st.button("Predict risk proxy"):
        payload = {
            "fiscal_year": int(fiscal_year),
            "wpp_haz_tp": phase_code,
            "work_mix_name": work_mix_api,
        }
        try:
            r = requests.post(f"{API_BASE.rstrip('/')}/predict", json=payload, timeout=15)
            if r.status_code != 200:
                detail = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
                st.error(f"API **{r.status_code}**: {detail}")
            else:
                data = r.json()
                score = data.get("predicted_risk_proxy")
                st.success("Prediction received.")
                st.metric("Predicted risk proxy", f"{score:.6f}" if score is not None else "—")
                with st.expander("Raw JSON"):
                    st.json(data)
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed (is the API running from `src/`?): {e}")

with col_right:
    st.subheader("Map")
    show_segments = st.toggle(
        "Show segments that match the criteria above",
        value=False,
        help="Off by default: only the study-area outline is shown.",
    )

    target_bucket = reduced_bucket_for_filter(work_mix_ui)
    if show_segments:
        sel = gdf_all[
            (gdf_all["FISCALYR"] == int(fiscal_year))
            & (gdf_all["WPPHAZTP"] == str(phase_code).strip().upper())
        ].copy()
        sel["_wm_bucket"] = sel["WPWKMIXN"].map(reduce_work_mix)
        sel = sel[sel["_wm_bucket"] == target_bucket]
        paths: list[dict] = []
        for _, row in sel.iterrows():
            pth = geom_to_lonlat_path(row.geometry)
            if not pth or len(pth) < 2:
                continue
            phase_d = row.get("WPPHAZTP_DESC")
            if phase_d is None or (isinstance(phase_d, (float, np.floating)) and np.isnan(phase_d)) or str(phase_d).strip() == "" or str(phase_d) == "nan":
                phase_d = wpp_haz_tp_to_desc(str(row.get("WPPHAZTP", ""))) or "—"
            paths.append(
                {
                    "path": pth,
                    "FISCALYR": int(row["FISCALYR"]) if pd.notna(row.get("FISCALYR")) else "—",
                    "phase_label": str(phase_d),
                    "work_mix_label": str(row.get("WPWKMIXN", "—")),
                    "risk_proxy": _format_tooltip_float(row.get("risk_proxy")),
                    "normalized_length": _format_tooltip_float(row.get("Normalized_Length")),
                    "phase_weight": _format_tooltip_float(row.get("PHASE_WEIGHT")),
                    "length": _format_tooltip_float(row.get("Shape__Length")),
                }
            )
        st.caption(f"**{len(paths):,}** segment(s) match fiscal year, phase, and work-mix bucket.")
    else:
        paths = []
        st.caption("Segments are hidden. Turn the toggle on to plot matches.")

    hull_bounds = unary_union(gdf_all.geometry.tolist()).convex_hull.bounds
    minx, miny, maxx, maxy = hull_bounds
    view = pdk.ViewState(
        latitude=float((miny + maxy) / 2),
        longitude=float((minx + maxx) / 2),
        zoom=9,
        pitch=0,
        bearing=0,
    )

    outline_layer = pdk.Layer(
        "GeoJsonLayer",
        data=study_area_geojson,
        stroked=True,
        filled=True,
        get_fill_color=[135, 206, 250, 40],
        get_line_color=[70, 130, 180, 180],
        line_width_min_pixels=2,
        pickable=False,
    )

    segment_layer = pdk.Layer(
        "PathLayer",
        data=paths,
        get_path="path",
        get_color=[220, 53, 69, 200],
        get_width=3,
        width_min_pixels=2,
        pickable=True,
    )

    layers = [outline_layer] + ([segment_layer] if paths else [])

    # PyDeck uses {{field}} on each path row; values are set in the `paths` dicts above.
    tooltip_cfg = None
    if paths:
        tooltip_cfg = {
            "text": f"""Year: {{FISCALYR}}
            Phase: {{phase_label}}
            Work mix: {{work_mix_label}}
            Risk Score: {{risk_proxy}}
            Normalized Length: {{normalized_length}}
            Project Length: {{length}}""",
        }
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style=pdk.map_styles.CARTO_LIGHT,
        tooltip=tooltip_cfg,
    )
    st.pydeck_chart(deck, width="stretch")
