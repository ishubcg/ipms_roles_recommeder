from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from fastapi import Request

from app.config import settings

_TRACKING_LOCK = Lock()

TRACKING_HEADERS = [
    "visitor_id",
    "session_id",
    "started_at",
    "last_activity_at",
    "session_duration_seconds",
    "ip_hash",
    "client_ip",
    "user_agent",
    "office_level",
    "vertical",
    "primary_role",
    "secondary_roles",
    "reached_level",
    "reached_vertical",
    "reached_daily_work",
    "reached_primary_role",
    "reached_secondary_roles",
    "reached_output",
    "downloaded_csv",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _tracking_dir() -> Path:
    path = Path(settings.tracking_data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def tracking_file_path() -> Path:
    return _tracking_dir() / settings.tracking_file_name


def _ensure_csv_exists() -> None:
    file_path = tracking_file_path()
    if file_path.exists():
        return

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKING_HEADERS)
        writer.writeheader()


def _read_rows() -> list[dict]:
    _ensure_csv_exists()
    file_path = tracking_file_path()

    with file_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_rows(rows: list[dict]) -> None:
    file_path = tracking_file_path()

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRACKING_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def _extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return ""


def _hash_ip(ip: str) -> str:
    if not ip:
        return ""
    raw = f"{settings.tracking_ip_salt}:{ip}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _to_int_flag(value) -> str:
    return "1" if bool(value) else "0"


def upsert_tracking_row(payload: dict, request: Request) -> dict:
    now = _utcnow()
    ip = _extract_client_ip(request)
    ip_hash = _hash_ip(ip)
    user_agent = request.headers.get("user-agent", "")

    visitor_id = str(payload.get("visitor_id", "")).strip()
    session_id = str(payload.get("session_id", "")).strip()

    if not visitor_id or not session_id:
        raise ValueError("visitor_id and session_id are required.")

    with _TRACKING_LOCK:
        rows = _read_rows()

        existing = None
        for row in rows:
            if row.get("session_id") == session_id:
                existing = row
                break

        if existing is None:
            existing = {
                "visitor_id": visitor_id,
                "session_id": session_id,
                "started_at": now.isoformat(),
                "last_activity_at": now.isoformat(),
                "session_duration_seconds": "0",
                "ip_hash": ip_hash,
                "client_ip": ip if settings.store_raw_ip else "",
                "user_agent": user_agent,
                "office_level": "",
                "vertical": "",
                "primary_role": "",
                "secondary_roles": "[]",
                "reached_level": "0",
                "reached_vertical": "0",
                "reached_daily_work": "0",
                "reached_primary_role": "0",
                "reached_secondary_roles": "0",
                "reached_output": "0",
                "downloaded_csv": "0",
            }
            rows.append(existing)

        started_at = datetime.fromisoformat(existing["started_at"])
        duration_seconds = int((now - started_at).total_seconds())

        existing["visitor_id"] = visitor_id
        existing["last_activity_at"] = now.isoformat()
        existing["session_duration_seconds"] = str(duration_seconds)
        existing["ip_hash"] = ip_hash
        existing["client_ip"] = ip if settings.store_raw_ip else ""
        existing["user_agent"] = user_agent

        existing["office_level"] = str(payload.get("office_level", "") or existing.get("office_level", "")).strip()
        existing["vertical"] = str(payload.get("vertical", "") or existing.get("vertical", "")).strip()
        existing["primary_role"] = str(payload.get("primary_role", "") or existing.get("primary_role", "")).strip()

        secondary_roles = payload.get("secondary_roles", [])
        if isinstance(secondary_roles, list):
            existing["secondary_roles"] = json.dumps(secondary_roles, ensure_ascii=False)

        existing["reached_level"] = _to_int_flag(
            int(existing.get("reached_level", "0")) or payload.get("reached_level")
        )
        existing["reached_vertical"] = _to_int_flag(
            int(existing.get("reached_vertical", "0")) or payload.get("reached_vertical")
        )
        existing["reached_daily_work"] = _to_int_flag(
            int(existing.get("reached_daily_work", "0")) or payload.get("reached_daily_work")
        )
        existing["reached_primary_role"] = _to_int_flag(
            int(existing.get("reached_primary_role", "0")) or payload.get("reached_primary_role")
        )
        existing["reached_secondary_roles"] = _to_int_flag(
            int(existing.get("reached_secondary_roles", "0")) or payload.get("reached_secondary_roles")
        )
        existing["reached_output"] = _to_int_flag(
            int(existing.get("reached_output", "0")) or payload.get("reached_output")
        )
        existing["downloaded_csv"] = _to_int_flag(
            int(existing.get("downloaded_csv", "0")) or payload.get("downloaded_csv")
        )

        _write_rows(rows)

    return existing