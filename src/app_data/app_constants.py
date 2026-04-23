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
    "2": "Active Construction (code 2)",
    "3": "Active Construction (code 3)",
    "6": "Active Construction (code 6)",
    "7": "Active Construction (code 7)",
}
