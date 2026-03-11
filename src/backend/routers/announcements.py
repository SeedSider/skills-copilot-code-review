"""Announcement endpoints for the High School Management System API."""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementInput(BaseModel):
    """Payload for creating and updating announcements."""

    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=1000)
    start_date: Optional[str] = None
    expiration_date: str


def _parse_iso_date(date_str: str, field_name: str) -> date:
    """Parse a YYYY-MM-DD date string and raise HTTP 400 when invalid."""

    try:
        return date.fromisoformat(date_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be in YYYY-MM-DD format (e.g., 2026-03-15)"
        ) from exc


def _validate_announcement_dates(start_date: Optional[str], expiration_date: str) -> Dict[str, Any]:
    """Validate required expiration date and optional start date ordering."""

    expiration = _parse_iso_date(expiration_date, "expiration_date")
    start: Optional[date] = None

    if start_date:
        start = _parse_iso_date(start_date, "start_date")

    if start and start > expiration:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after expiration_date"
        )

    return {
        "start_date": start_date,
        "expiration_date": expiration_date
    }


def _ensure_teacher_authenticated(teacher_username: Optional[str]) -> None:
    """Enforce that the request includes a valid signed-in teacher username."""

    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")


def _parse_announcement_id(announcement_id: str) -> ObjectId:
    """Convert string id to ObjectId and raise HTTP 400 for invalid values."""

    try:
        return ObjectId(announcement_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements(active_only: bool = Query(True)) -> List[Dict[str, Any]]:
    """Get announcements, optionally filtered to currently active announcements."""

    today = date.today().isoformat()

    if active_only:
        query = {
            "$and": [
                {"expiration_date": {"$gte": today}},
                {
                    "$or": [
                        {"start_date": {"$exists": False}},
                        {"start_date": None},
                        {"start_date": ""},
                        {"start_date": {"$lte": today}}
                    ]
                }
            ]
        }
    else:
        query = {}

    docs = announcements_collection.find(query).sort("expiration_date", 1)
    return [
        {
            "id": str(doc.get("_id")),
            "title": doc.get("title", ""),
            "message": doc.get("message", ""),
            "start_date": doc.get("start_date"),
            "expiration_date": doc.get("expiration_date")
        }
        for doc in docs
    ]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementInput, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement (signed-in teachers only)."""

    _ensure_teacher_authenticated(teacher_username)
    validated_dates = _validate_announcement_dates(payload.start_date, payload.expiration_date)
    title = payload.title.strip()
    message = payload.message.strip()

    if not title or not message:
        raise HTTPException(status_code=400, detail="title and message cannot be empty")

    result = announcements_collection.insert_one(
        {
            "title": title,
            "message": message,
            "start_date": validated_dates["start_date"],
            "expiration_date": validated_dates["expiration_date"]
        }
    )

    return {
        "message": "Announcement created successfully",
        "id": str(result.inserted_id)
    }


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementInput,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an announcement (signed-in teachers only)."""

    _ensure_teacher_authenticated(teacher_username)
    validated_dates = _validate_announcement_dates(payload.start_date, payload.expiration_date)
    object_id = _parse_announcement_id(announcement_id)
    title = payload.title.strip()
    message = payload.message.strip()

    if not title or not message:
        raise HTTPException(status_code=400, detail="title and message cannot be empty")

    result = announcements_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "title": title,
                "message": message,
                "start_date": validated_dates["start_date"],
                "expiration_date": validated_dates["expiration_date"]
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement updated successfully"}


@router.delete("/{announcement_id}", response_model=Dict[str, Any])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Delete an announcement (signed-in teachers only)."""

    _ensure_teacher_authenticated(teacher_username)
    object_id = _parse_announcement_id(announcement_id)

    result = announcements_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
