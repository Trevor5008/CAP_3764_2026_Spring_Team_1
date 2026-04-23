"""
Streamlit demo: risk-proxy prediction + optional map of FDOT segments (Miami-Dade).

Run from `src/`: streamlit run app.py
API: from `src/`: uvicorn main:app --reload
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from shapely.ops import unary_union

from app_data.app_constants import DEFAULT_API_BASE, OTHER_WORK_MIX_SENTINEL, PHASE_CHOICES, WORK_MIX_DISPLAY_LABELS
from app_data.construction_data import load_construction_gdf
from app_data.features import WORK_MIX_TOP12_LABELS, reduce_work_mix, wpp_haz_tp_to_desc
from components.app_filters import phase_codes_for_filter, reduced_bucket_for_filter, work_mix_for_api
from components.geometry_utils import geom_to_lonlat_path
from components.risk_viz import (
    format_tooltip_float,
    risk_proxy_color,
    risk_scale_from_series,
    segment_tooltip_html,
)

API_BASE = DEFAULT_API_BASE
ALL_YEARS_SENTINEL = "__ALL_YEARS__"
ALL_PHASES_SENTINEL = "__ALL_PHASES__"
ALL_WORK_MIX_SENTINEL = "__ALL_WORK_MIX__"
WORK_MIX_DISPLAY_LABELS: dict[str, str] = {
    "ADD LANES & RECONSTR": "ADD LANES & RECONSTRUCTION",
    "BRIDGE-REPLACE AND A": "BRIDGE-REPLACE AND ADD LANES",
    "FLEXIBLE PAVEMENT RE": "FLEXIBLE PAVEMENT REHAB",
    "INTERCHANGE - ADD LA": "INTERCHANGE - ADD LANES",
    "INTERCHANGE RAMP (NE": "INTERCHANGE RAMP (NEAR EXIT)",
    "ITS FREEWAY MANAGEME": "ITS FREEWAY MANAGEMENT",
    "PEDESTRIAN SAFETY IM": "PEDESTRIAN SAFETY IMPROVEMENT",
    "RIGID PAVEMENT RECON": "RIGID PAVEMENT RECONSTRUCTION",
    "RIGID PAVEMENT REHAB": "RIGID PAVEMENT REHABILITATION",
}

st.set_page_config(
    page_title="CAP 3764 — Risk proxy",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("CAP 3764 — FDOT risk proxy visualizer")
st.caption(
    "Miami-Dade Work Program construction segments (EPSG:4326). This is a visualizer for the risk proxy model. "
    "Map segments stay hidden until you turn them on. "
    "The map displays the segments that match the criteria above."
)

gdf_all = load_construction_gdf()

# Wide page + map-heavy split: left ~28%, right ~72% of main content
col_left, col_right = st.columns([1.0, 2.6], gap="large")

with col_left:
    st.subheader("Inputs")
    fiscal_year_options = sorted(
        int(v) for v in pd.to_numeric(gdf_all["FISCALYR"], errors="coerce").dropna().astype(int).unique().tolist()
    )
    fiscal_year_ui = st.selectbox(
        "Fiscal year",
        options=[ALL_YEARS_SENTINEL] + fiscal_year_options,
        format_func=lambda y: "All years" if y == ALL_YEARS_SENTINEL else str(y),
        index=0,
    )
    phase_code = st.selectbox(
        "Construction phase (WPPHAZTP)",
        options=[ALL_PHASES_SENTINEL] + list(PHASE_CHOICES.keys()),
        format_func=lambda c: "All phases" if c == ALL_PHASES_SENTINEL else PHASE_CHOICES[c],
        index=0,
    )
    work_options = [ALL_WORK_MIX_SENTINEL] + list(WORK_MIX_TOP12_LABELS) + [OTHER_WORK_MIX_SENTINEL]
    work_mix_ui = st.selectbox(
        "Work mix (WPWKMIXN, training top-12 + Other)",
        options=work_options,
        format_func=lambda x: (
            "All work mix"
            if x == ALL_WORK_MIX_SENTINEL
            else (
                "Other (anything outside top-12)"
                if x == OTHER_WORK_MIX_SENTINEL
                else WORK_MIX_DISPLAY_LABELS.get(x, x)
            )
        ),
        index=0,
    )
    can_predict = (
        fiscal_year_ui != ALL_YEARS_SENTINEL
        and phase_code != ALL_PHASES_SENTINEL
        and work_mix_ui != ALL_WORK_MIX_SENTINEL
    )
    work_mix_api = work_mix_for_api(work_mix_ui) if work_mix_ui != ALL_WORK_MIX_SENTINEL else ""

    if not can_predict:
        st.caption("Prediction requires specific values. Choose concrete year, phase, and work mix.")
    if st.button("Predict risk proxy", disabled=not can_predict):
        payload = {
            "fiscal_year": int(fiscal_year_ui),
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

    target_bucket = None if work_mix_ui == ALL_WORK_MIX_SENTINEL else reduced_bucket_for_filter(work_mix_ui)
    phase_codes = (
        tuple(sorted(gdf_all["WPPHAZTP"].dropna().astype(str).str.strip().str.upper().unique()))
        if phase_code == ALL_PHASES_SENTINEL
        else phase_codes_for_filter(phase_code)
    )
    if show_segments:
        sel = gdf_all.copy()
        if fiscal_year_ui != ALL_YEARS_SENTINEL:
            sel = sel[sel["FISCALYR"] == int(fiscal_year_ui)]
        sel = sel[sel["WPPHAZTP"].isin(phase_codes)]
        if target_bucket is not None:
            sel["_wm_bucket"] = sel["WPWKMIXN"].map(reduce_work_mix)
            sel = sel[sel["_wm_bucket"] == target_bucket]
        r_lo, r_hi = risk_scale_from_series(sel["risk_proxy"]) if "risk_proxy" in sel.columns else (0.0, 1.0)
        paths: list[dict] = []
        for _, row in sel.iterrows():
            pth = geom_to_lonlat_path(row.geometry)
            if not pth or len(pth) < 2:
                continue
            phase_d = row.get("WPPHAZTP_DESC")
            if phase_d is None or (isinstance(phase_d, (float, np.floating)) and np.isnan(phase_d)) or str(phase_d).strip() == "" or str(phase_d) == "nan":
                phase_d = wpp_haz_tp_to_desc(str(row.get("WPPHAZTP", ""))) or "—"
            risk = row.get("risk_proxy")
            color = risk_proxy_color(risk, r_lo, r_hi)
            tip = {
                "FISCALYR": int(row["FISCALYR"]) if pd.notna(row.get("FISCALYR")) else "—",
                "phase_label": str(phase_d),
                "work_mix_label": str(row.get("WPWKMIXN", "—")),
                "risk_proxy": format_tooltip_float(risk),
                "normalized_length": format_tooltip_float(row.get("Normalized_Length")),
                "phase_weight": format_tooltip_float(row.get("PHASE_WEIGHT")),
                "length": format_tooltip_float(row.get("Shape__Length")),
            }
            paths.append(
                {
                    "path": pth,
                    "color": color,
                    "tooltip_html": segment_tooltip_html(tip),
                    **tip,
                }
            )
        st.caption(
            f"**{len(paths):,}** segment(s) match the selected criteria. "
            f"Segment color encodes **risk_proxy** on this filter’s range **{r_lo:.4f}** → **{r_hi:.4f}** "
            f"(green / yellow toward low values, orange / red toward high; missing values are gray)."
        )
    else:
        paths = []
        r_lo, r_hi = 0.0, 1.0
        st.caption("Segments are hidden. Turn the toggle on to plot matches.")

    hull_bounds = unary_union(gdf_all.geometry.tolist()).convex_hull.bounds
    minx, miny, maxx, maxy = hull_bounds
    view = pdk.ViewState(
        latitude=float((miny + maxy) / 2),
        longitude=float((minx + maxx) / 2),
        zoom=9,
        pitch=20 if paths else 12,
        bearing=0,
    )

    outline_layer = pdk.Layer(
        "GeoJsonLayer",
        data=gdf_all.geometry.tolist(),
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
        get_color="color",
        get_width=3,
        width_min_pixels=2,
        pickable=True,
    )

    layers = [outline_layer] + ([segment_layer] if paths else [])

    tooltip_cfg = None
    if paths:
        tooltip_cfg = {"html": "{tooltip_html}"}
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style=pdk.map_styles.CARTO_LIGHT,
        tooltip=tooltip_cfg,
    )
    st.pydeck_chart(deck, width="stretch")
