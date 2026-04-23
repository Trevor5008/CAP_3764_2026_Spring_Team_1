"""Map/API filter value normalization (Streamlit selections → model + GeoDataFrame logic)."""

from __future__ import annotations

from app_data.app_constants import OTHER_WORK_MIX_SENTINEL
from app_data.features import reduce_work_mix


def work_mix_for_api(ui_value: str) -> str:
    if ui_value == OTHER_WORK_MIX_SENTINEL:
        return "UNLISTED_WORK_MIX"
    return ui_value


def reduced_bucket_for_filter(ui_value: str) -> str:
    if ui_value == OTHER_WORK_MIX_SENTINEL:
        return "Other"
    return reduce_work_mix(ui_value)
