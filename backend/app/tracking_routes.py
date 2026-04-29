from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.tracking_service import tracking_file_path, upsert_tracking_row

router = APIRouter()


class TrackingSnapshotRequest(BaseModel):
    visitor_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)

    office_level: str = ""
    vertical: str = ""
    primary_role: str = ""
    secondary_roles: list[str] = Field(default_factory=list)

    reached_level: int = 0
    reached_vertical: int = 0
    reached_daily_work: int = 0
    reached_primary_role: int = 0
    reached_secondary_roles: int = 0
    reached_output: int = 0
    downloaded_csv: int = 0


@router.post("/snapshot")
def save_tracking_snapshot(payload: TrackingSnapshotRequest, request: Request):
    try:
        row = upsert_tracking_row(payload.model_dump(), request)
        return {"ok": True, "session_id": row["session_id"]}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/export")
def export_tracking_csv():
    file_path = tracking_file_path()
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=file_path.name,
    )