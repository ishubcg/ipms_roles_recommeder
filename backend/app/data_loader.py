from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from app.config import LEVELS_ORDERED, settings


@lru_cache(maxsize=1)
def load_data() -> list[dict]:
    with open(settings.kpi_data_path, "r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache(maxsize=1)
def get_levels() -> List[str]:
    data = load_data()
    present = {row["level"] for row in data}
    ordered = [level for level in LEVELS_ORDERED if level in present]
    extras = sorted(present - set(LEVELS_ORDERED))
    return ordered + extras


@lru_cache(maxsize=64)
def get_verticals(level: str) -> List[str]:
    data = load_data()
    filtered = [row for row in data if row["level"] == level]
    return sorted({row["vertical"] for row in filtered})


@lru_cache(maxsize=256)
def get_roles(level: str, vertical: str) -> List[dict]:
    data = load_data()
    filtered = [row for row in data if row["level"] == level and row["vertical"] == vertical]

    merged: dict[str, dict] = {}
    for row in filtered:
        role_name = row["role"]

        if role_name not in merged:
            merged[role_name] = {
                "role": role_name,
                "hrms_role_name": row.get("hrms_role_name", ""),
                "role_description": row.get("role_description", ""),
                "level": level,
                "vertical": vertical,
                "kpis": [],
            }
        else:
            if not merged[role_name].get("hrms_role_name") and row.get("hrms_role_name"):
                merged[role_name]["hrms_role_name"] = row.get("hrms_role_name", "")
            if not merged[role_name].get("role_description") and row.get("role_description"):
                merged[role_name]["role_description"] = row.get("role_description", "")

        merged[role_name]["kpis"].extend(row["kpis"])

    return list(merged.values())