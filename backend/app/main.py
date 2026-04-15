from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import LEVEL_LABELS, MAX_SECONDARY_ROLES, settings
from app.data_loader import get_levels, get_verticals
from app.models import BootstrapResponse, LevelOption, RecommendationRequest, RecommendationResponse, RoleItem, VerticalResponse
from app.recommendation_service import recommend_roles_for_vertical

app = FastAPI(title="KPI Selector API", version="1.0.0")

allowed_origins = [
    settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/bootstrap", response_model=BootstrapResponse)
def bootstrap() -> BootstrapResponse:
    levels = [
        LevelOption(label=LEVEL_LABELS.get(level, level), value=level)
        for level in get_levels()
    ]
    return BootstrapResponse(levels=levels, max_secondary_roles=MAX_SECONDARY_ROLES)


@app.get("/api/verticals", response_model=VerticalResponse)
def verticals(level: str = Query(...)) -> VerticalResponse:
    return VerticalResponse(level=level, verticals=get_verticals(level))


@app.post("/api/recommendations", response_model=RecommendationResponse)
def recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    recommendations, used_llm = recommend_roles_for_vertical(
        level=payload.level,
        vertical=payload.vertical,
        daily_work=payload.daily_work,
        exclude_roles=payload.exclude_roles,
        top_k=payload.top_k,
    )
    return RecommendationResponse(
        level=payload.level,
        vertical=payload.vertical,
        daily_work=payload.daily_work,
        used_llm=used_llm,
        recommendations=[RoleItem(**item) for item in recommendations],
    )
