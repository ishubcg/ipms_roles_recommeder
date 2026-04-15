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
        "short role name",
        "role description",
        "kpi",
        "short kpis",
    }

    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in master_data.xlsx: {sorted(missing)}")

    grouped: dict[tuple[str, str, str, str, str], list[dict]] = {}

    for _, row in df.iterrows():
        vertical = _clean(row["vertical"])
        level = _clean(row["level"])
        role = _clean(row["role name"])
        short_role_name = _clean(row["short role name"])
        role_description = _clean(row["role description"])
        kpi = _clean(row["kpi"])
        short_kpi = _clean(row["short kpis"])

        if not kpi:
            continue

        key = (vertical, level, role, short_role_name, role_description)
        grouped.setdefault(key, []).append(
            {
                "kpi": kpi,
                "short_kpi": short_kpi,
            }
        )

    records = [
        {
            "vertical": vertical,
            "level": level,
            "role": role,
            "short_role_name": short_role_name,
            "role_description": role_description,
            "kpis": kpis,
        }
        for (vertical, level, role, short_role_name, role_description), kpis in grouped.items()
    ]

    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    print(f"Saved {len(records)} role entries to {OUTPUT_JSON}")


if __name__ == "__main__":
    convert()