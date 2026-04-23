"""Risk-proxy coloring and tooltips."""

from __future__ import annotations

import html

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import numpy as np
import pandas as pd


# Helper function to format a tooltip for a segment
def segment_tooltip_html(tip: dict) -> str:
    """
    Fully rendered HTML for one PathLayer row. Deck's built-in tooltip template
    often fails to substitute `{{field}}` in Streamlit/pydeck; a single `{tooltip_html}`
    accessor avoids that.
    """
    rows = [
        ("Year", tip.get("FISCALYR", "—")),
        ("Phase", tip.get("phase_label", "—")),
        ("Work mix", tip.get("work_mix_label", "—")),
        ("Risk score", tip.get("risk_proxy", "—")),
        ("Normalized length", tip.get("normalized_length", "—")),
        ("Phase weight", tip.get("phase_weight", "—")),
        ("Project length", tip.get("length", "—")),
    ]
    parts = [f"<b>{html.escape(str(lbl))}</b>: {html.escape(str(val))}" for lbl, val in rows]
    return "<br/>".join(parts)

# Helper function to format a float value for a tooltip
def format_tooltip_float(value, nd: int = 4) -> str:
    if value is None or (isinstance(value, (float, np.floating)) and (np.isnan(value) or np.isinf(value))):
        return "—"
    if isinstance(value, (int, float, np.integer, np.floating)) and pd.isna(value):
        return "—"
    try:
        return f"{float(value):.{nd}f}"
    except (TypeError, ValueError):
        return "—"

# Helper function to get the color for a risk value
def risk_proxy_color(risk: object, vmin: float, vmax: float) -> list[int]:
    """RGBA for PathLayer: low risk_proxy → green/yellow, high → red (RdYlGn_r)."""
    gray = [140, 140, 140, 200]
    try:
        v = float(risk)
    except (TypeError, ValueError):
        return gray
    if not np.isfinite(v) or np.isnan(v):
        return gray
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        return gray
    if vmax <= vmin:
        t = 0.5
    else:
        t = float(np.clip((v - vmin) / (vmax - vmin), 0.0, 1.0))
    cmap = mpl.colormaps["RdYlGn_r"]
    r, g, b, _ = cmap(t)
    return [int(r * 255), int(g * 255), int(b * 255), 230]

# Helper function to get the risk scale from a series of risk values (used to normalize the risk values)
def risk_scale_from_series(risk_series: pd.Series) -> tuple[float, float]:
    vals = pd.to_numeric(risk_series, errors="coerce").dropna()
    if vals.empty:
        return 0.0, 1.0
    lo, hi = float(vals.min()), float(vals.max())
    if hi <= lo:
        lo, hi = lo - 1e-9, hi + 1e-9
    return lo, hi
