from __future__ import annotations

from rapidfuzz import fuzz

from app.config import settings
from app.data_loader import get_roles
from app.llm_service import LLMUnavailableError, call_json
from app.search_service import normalize


def _candidate_payload(role: dict) -> dict:
    return {
        "role": role["role"],
        "short_role_name": role.get("short_role_name", ""),
        "role_description": role.get("role_description", ""),
        "level": role["level"],
        "vertical": role["vertical"],
        "kpis": [k["kpi"] for k in role["kpis"]],
        "short_kpis": [k.get("short_kpi", "") for k in role["kpis"]],
    }


def _llm_recommend(work_text: str, candidates: list[dict], top_k: int) -> list[dict]:
    system_prompt = (
        "You are an expert role recommendation engine. "
        "Map a user's daily work description to the most relevant roles. "
        "Use Role Name, Short Role Name, and Role Description as the primary signal. "
        "Use KPI information only as supporting context. "
        "Return strict JSON only."
    )

    candidate_payload = [_candidate_payload(role) for role in candidates]

    user_prompt = (
        "User daily work description:\n"
        f"{work_text}\n\n"
        "Candidate roles:\n"
        f"{candidate_payload}\n\n"
        f"Return a JSON object with a key 'recommendations' containing up to {top_k} items. "
        "Each item must have: role, relevance_score (0-100), reason. "
        "Only recommend roles from the provided candidate list. "
        "Base the ranking mainly on role title and role description."
    )

    response = call_json(system_prompt, user_prompt)
    recommendations = response.get("recommendations", []) if isinstance(response, dict) else []

    role_lookup = {role["role"]: role for role in candidates}
    merged = []

    for item in recommendations:
        role_name = item.get("role")
        if role_name not in role_lookup:
            continue

        base = role_lookup[role_name]
        merged.append(
            {
                **base,
                "relevance_score": float(item.get("relevance_score", 0.0)),
                "reason": str(item.get("reason", "")).strip(),
                "matched_kpis": [],
            }
        )

    merged.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
    return merged[:top_k]


def _fallback_recommend(work_text: str, candidates: list[dict], top_k: int) -> list[dict]:
    query = normalize(work_text)
    scored = []

    for role in candidates:
        role_name_score = fuzz.token_set_ratio(query, normalize(role["role"])) / 100.0
        short_role_name_score = fuzz.token_set_ratio(
            query,
            normalize(role.get("short_role_name", "")),
        ) / 100.0
        role_description_score = fuzz.token_set_ratio(
            query,
            normalize(role.get("role_description", "")),
        ) / 100.0

        final_score = round(
            (
                role_description_score * 0.55
                + role_name_score * 0.30
                + short_role_name_score * 0.15
            )
            * 100,
            2,
        )

        if role_description_score >= 0.45 or role_name_score >= 0.45 or short_role_name_score >= 0.45:
            reason = "Matched role title and role description from your daily work description."
        else:
            reason = "Broad similarity to the role title and responsibilities described."

        scored.append(
            {
                **role,
                "relevance_score": final_score,
                "reason": reason,
                "matched_kpis": [],
            }
        )

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored[:top_k]


def recommend_roles_for_vertical(
    level: str,
    vertical: str,
    daily_work: str,
    exclude_roles: list[str] | None = None,
    top_k: int | None = None,
) -> tuple[list[dict], bool]:
    exclude_roles = exclude_roles or []
    top_k = top_k or settings.role_recommendation_top_k

    candidates = [
        role for role in get_roles(level, vertical)
        if role["role"] not in set(exclude_roles)
    ]

    if not candidates:
        print("[recommendation_service] No candidate roles found.")
        return [], False

    print(f"[recommendation_service] Candidates found: {len(candidates)}")
    print(f"[recommendation_service] LLM enabled: {settings.enable_llm_recommender}")
    print(f"[recommendation_service] LLM provider: '{settings.llm_provider}'")
    print(f"[recommendation_service] Groq key present: {bool(settings.groq_api_key)}")

    if settings.enable_llm_recommender:
        try:
            print("[recommendation_service] Attempting LLM recommendation...")
            results = _llm_recommend(daily_work, candidates, top_k)
            print("[recommendation_service] LLM recommendation succeeded.")
            return results, True
        except LLMUnavailableError as exc:
            print(f"[recommendation_service] LLM unavailable: {exc}")
        except Exception as exc:
            print(f"[recommendation_service] LLM failed, using fallback. Error: {exc}")

    print("[recommendation_service] Using fallback recommendation engine.")
    return _fallback_recommend(daily_work, candidates, top_k), False