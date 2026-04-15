from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class KPIItem(BaseModel):
    kpi: str
    short_kpi: str = Field(default="")


class RoleItem(BaseModel):
    vertical: str
    role: str
    short_role_name: str = Field(default="")
    role_description: str = Field(default="")
    level: str
    kpis: List[KPIItem]
    relevance_score: float = 0.0
    reason: str = ""
    matched_kpis: List[str] = Field(default_factory=list)


class LevelOption(BaseModel):
    label: str
    value: str


class RecommendationRequest(BaseModel):
    level: str
    vertical: str
    daily_work: str
    exclude_roles: List[str] = Field(default_factory=list)
    top_k: Optional[int] = None


class RecommendationResponse(BaseModel):
    level: str
    vertical: str
    daily_work: str
    recommendations: List[RoleItem]
    used_llm: bool = False


class BootstrapResponse(BaseModel):
    levels: List[LevelOption]
    max_secondary_roles: int


class VerticalResponse(BaseModel):
    level: str
    verticals: List[str]