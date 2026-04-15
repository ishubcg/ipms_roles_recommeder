from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
ENV_PATH = ROOT_DIR / "backend" / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    llm_provider: str = os.getenv("LLM_PROVIDER", "").strip().lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    role_recommendation_top_k: int = int(os.getenv("ROLE_RECOMMENDATION_TOP_K", "12"))
    enable_llm_recommender: bool = os.getenv("ENABLE_LLM_RECOMMENDER", "true").strip().lower() == "true"

    kpi_data_path: Path = Path(os.getenv("KPI_DATA_PATH", DATA_DIR / "kpi_data.json"))
    master_data_path: Path = Path(os.getenv("MASTER_DATA_PATH", DATA_DIR / "master_data.xlsx"))


LEVELS_ORDERED = [
    "Corporate",
    "Circle",
    "BA",
    "OA",
    "Circle office",
    "BA office",
    "Platinum Unit",
    "Gold Unit",
    "CNTX- Circle",
    "CNTX- TR BA",
    "Corporate office",
    "Contract labour & Absorption cases",
    "Circle & BA",
    "Corporate office, Circle & BA",
]

LEVEL_LABELS = {
    "Corporate": "Corporate",
    "Circle": "Circle",
    "BA": "BA (Business Area)",
    "OA": "OA (Operating Area)",
    "Circle office": "Circle Office",
    "BA office": "BA Office",
    "Platinum Unit": "Platinum Unit",
    "Gold Unit": "Gold Unit",
    "CNTX- Circle": "CNTX - Circle",
    "CNTX- TR BA": "CNTX - TR BA",
    "Corporate office": "Corporate Office",
    "Contract labour & Absorption cases": "Contract Labour & Absorption Cases",
    "Circle & BA": "Circle & BA",
    "Corporate office, Circle & BA": "Corporate Office, Circle & BA",
}

MAX_SECONDARY_ROLES = 4
settings = Settings()
