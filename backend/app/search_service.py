from __future__ import annotations


def normalize(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def filter_roles_by_name(query: str, roles: list[dict]) -> list[dict]:
    if not query or not query.strip():
        return roles

    q = normalize(query)
    starts_with = []
    contains = []

    for role in roles:
        role_name = normalize(role.get("role", ""))
        if role_name.startswith(q):
            starts_with.append(role)
        elif q in role_name:
            contains.append(role)

    return starts_with + contains
