"""Shared constants for the Streamlit app and small helpers (paths, phase labels)."""

from __future__ import annotations

from pathlib import Path

# Repository `src/` root (this file lives in `src/app_data/`)
_SRC_ROOT = Path(__file__).resolve().parent.parent

GPKG_PATH = _SRC_ROOT / "data/processed/fdot_work_program_construction.gpkg"
RISK_CSV_PATH = _SRC_ROOT / "data/processed/construction_with_risk_proxy.csv"

DEFAULT_API_BASE = "http://127.0.0.1:8000"

# UI value that buckets to "Other" for API + map filters
OTHER_WORK_MIX_SENTINEL = "__OTHER_BUCKET__"

PHASE_CHOICES: dict[str, str] = {
    "4": "Contract Executed (code 4)",
    "8": "Pre-Construction (code 8)",
    "A": "Construction Completed (code A)",
    "2": "Active Construction (codes 2/3/6/7)",
}

# App-level grouped phase semantics:
# - "2" is the single UI/API representative for active construction.
# - Map filtering should include all active codes when "2" is selected.
ACTIVE_CONSTRUCTION_PHASE_CODES: tuple[str, ...] = ("2", "3", "6", "7")

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