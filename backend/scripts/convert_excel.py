from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
MASTER_DATA = DATA_DIR / "master_data.xlsx"
OUTPUT_JSON = DATA_DIR / "kpi_data.json"


def _clean(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def convert() -> None:
    df = pd.read_excel(MASTER_DATA)
    df.columns = [c.strip().lower() for c in df.columns]

    required_columns = {
        "vertical",
        "level",
        "role name",
        "hrms role name",
        "role description",
        "kpi",
        "hrms kpi name",
        "kpis priority",
    }

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in master_data.xlsx: {sorted(missing)}")

    grouped: dict[tuple[str, str, str, str, str], list[dict]] = {}

    for _, row in df.iterrows():
        vertical = _clean(row["vertical"])
        level = _clean(row["level"])
        role = _clean(row["role name"])
        hrms_role_name = _clean(row["hrms role name"])
        role_description = _clean(row["role description"])
        kpi = _clean(row["kpi"])
        hrms_kpi_name = _clean(row["hrms kpi name"])
        kpi_priority = _clean(row["kpis priority"])

        if not vertical or not level or not role or not kpi:
            continue

        key = (vertical, level, role, hrms_role_name, role_description)
        grouped.setdefault(key, []).append(
            {
                "kpi": kpi,
                "hrms_kpi_name": hrms_kpi_name,
                "kpi_priority": kpi_priority,
            }
        )

    records = [
        {
            "vertical": vertical,
            "level": level,
            "role": role,
            "hrms_role_name": hrms_role_name,
            "role_description": role_description,
            "kpis": kpis,
        }
        for (vertical, level, role, hrms_role_name, role_description), kpis in grouped.items()
    ]

    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(records)} role entries to {OUTPUT_JSON}")


if __name__ == "__main__":
    convert()