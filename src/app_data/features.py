"""
Feature row for rf_model.pkl (baseline_no_length pipeline).

Mirrors src/models/baseline_no_length.ipynb: TOP_K work-mix reduction,
WPPHAZTP -> WPPHAZTP_DESC, then one-hot alignment with training drop_first.
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd

# Same legend as analysis/risk-proxy.ipynb
PHASE_TYPE_LEGEND: dict[str, str] = {
    "2": "Active Construction",
    "3": "Active Construction",
    "4": "Contract Executed",
    "6": "Active Construction",
    "7": "Active Construction",
    "8": "Pre-Construction",
    "A": "Construction Completed",
}

# Fixed TOP_K=12 set from construction_with_risk_proxy.csv (baseline_no_length).
# Keep these as raw WPWKMIXN values (often truncated) so API/model/map filtering
# all align to the encoded training categories.
_WORK_MIX_TOP12 = frozenset(
    {
        "ADD LANES & RECONSTR",
        "BIKE PATH/TRAIL",
        "BRIDGE-REPLACE AND A",
        "FLEXIBLE PAVEMENT RE",
        "INTERCHANGE - ADD LA",
        "INTERCHANGE RAMP (NE",
        "INTERSECTION IMPROVE",
        "ITS FREEWAY MANAGEME",
        "PEDESTRIAN SAFETY IM",
        "RESURFACING",
        "RIGID PAVEMENT RECON",
        "RIGID PAVEMENT REHAB",
    }
)

# Columns after pd.get_dummies(..., drop_first=True) — "Active Construction" and
# "ADD LANES & RECONSTR" are reference levels (all zeros in row).
_PHASE_DUMMY_PREFIX = "WPPHAZTP_DESC_"
_WORK_MIX_DUMMY_PREFIX = "work_mix_reduced_"

# UI / API: canonical WPWKMIXN labels in the training top-12 (sorted for stable pickers)
WORK_MIX_TOP12_LABELS: tuple[str, ...] = tuple(sorted(_WORK_MIX_TOP12))

_WORK_MIX_ALIASES: dict[str, str] = {
    "ADD LANES & RECONSTRUCTION": "ADD LANES & RECONSTR",
    "BRIDGE-REPLACE AND ADD LANES": "BRIDGE-REPLACE AND A",
    "FLEXIBLE PAVEMENT REHAB": "FLEXIBLE PAVEMENT RE",
    "INTERCHANGE - ADD LANES": "INTERCHANGE - ADD LA",
    "INTERCHANGE RAMP (NEAR EXIT)": "INTERCHANGE RAMP (NE",
    "ITS FREEWAY MANAGEMENT": "ITS FREEWAY MANAGEME",
    "PEDESTRIAN SAFETY IMPROVEMENT": "PEDESTRIAN SAFETY IM",
    "RIGID PAVEMENT RECONSTRUCTION": "RIGID PAVEMENT RECON",
    "RIGID PAVEMENT REHABILITATION": "RIGID PAVEMENT REHAB",
}


def wpp_haz_tp_to_desc(code: str) -> str | None:
    key = str(code).strip().upper() if code else ""
    return PHASE_TYPE_LEGEND.get(key)


def reduce_work_mix(wpwkmixn: str) -> str:
    name = str(wpwkmixn).strip()
    name = _WORK_MIX_ALIASES.get(name, name)
    if name in _WORK_MIX_TOP12:
        return name
    return "Other"


def build_feature_frame(
    fiscal_year: int,
    wpp_haz_tp: str,
    work_mix_name: str,
    feature_names: Sequence[str],
) -> pd.DataFrame:
    """
    Single-row DataFrame with columns exactly matching the trained RF's feature_names_in_.
    """
    phase_desc = wpp_haz_tp_to_desc(wpp_haz_tp)
    if phase_desc is None:
        raise ValueError(
            f"Unknown WPPHAZTP code {wpp_haz_tp!r}; "
            f"expected one of {sorted(PHASE_TYPE_LEGEND.keys())}"
        )

    wmr = reduce_work_mix(work_mix_name)

    row: dict[str, float] = {str(c): 0.0 for c in feature_names}

    if "FISCALYR" not in row:
        raise ValueError("Model is missing FISCALYR column")

    row["FISCALYR"] = float(fiscal_year)

    pcol = f"{_PHASE_DUMMY_PREFIX}{phase_desc}"
    if pcol in row:
        row[pcol] = 1.0

    wcol = f"{_WORK_MIX_DUMMY_PREFIX}{wmr}"
    if wcol in row:
        row[wcol] = 1.0

    ordered = [row[str(c)] for c in feature_names]
    return pd.DataFrame([ordered], columns=[str(c) for c in feature_names])
