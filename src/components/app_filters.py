"""Map/API filter value normalization (Streamlit selections → model + GeoDataFrame logic)."""

from __future__ import annotations

from app_data.app_constants import ACTIVE_CONSTRUCTION_PHASE_CODES, OTHER_WORK_MIX_SENTINEL
from app_data.features import reduce_work_mix

# Helper function that converts UI value for "other work mix" to the API value
def work_mix_for_api(ui_value: str) -> str:
    return "UNLISTED_WORK_MIX" if ui_value == OTHER_WORK_MIX_SENTINEL else ui_value

# Helper function that converts UI value for "other work mix" to the GeoDataFrame value
def reduced_bucket_for_filter(ui_value: str) -> str:
    return "Other" if ui_value == OTHER_WORK_MIX_SENTINEL else reduce_work_mix(ui_value)

# Helper function that converts UI value for "active construction" to the GeoDataFrame value
def phase_codes_for_filter(ui_phase_code: str) -> tuple[str, ...]:
    return ACTIVE_CONSTRUCTION_PHASE_CODES if ui_phase_code == "2" else (ui_phase_code,)
