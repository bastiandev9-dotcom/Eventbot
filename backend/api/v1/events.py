"""
Events Endpoints
================
Endpoint untuk CRUD event, pencarian, dan rekomendasi.
"""

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.services import EventService, RecommendationService
from backend.api.deps import require_auth

router = APIRouter(prefix="/events", tags=["Events"])


# ── Request Schemas ───────────────────────────────────────

class CreateEventRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=255, example="Tech Conference 2026")
    description: str = Field(..., example="Konferensi teknologi tahunan")
    short_description: str = Field(..., max_length=500, example="Event teknologi terbesar")
    start_date: str = Field(..., example="2026-08-01")
    end_date: str = Field(..., example="2026-08-02")
    start_time: Optional[str] = Field(None, example="09:00")
    end_time: Optional[str] = Field(None, example="17:00")
    location: str = Field(..., example="Jakarta Convention Center")
    location_map_url: Optional[str] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None
    capacity: Optional[int] = Field(0, ge=0)
    status: Optional[str] = Field("upcoming", example="upcoming")
    is_published: Optional[bool] = False


class UpdateEventRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    location_map_url: Optional[str] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    is_published: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────

def _get_auth_user(authorization: Optional[str]):
    """Ekstrak dan validasi user dari Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan")
    token = authorization.split(" ", 1)[1]
    try:
        return require_auth(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ── Endpoints ─────────────────────────────────────────────

@router.get("/")
async def list_events(
    q: Optional[str] = Query(None, description="Keyword pencarian"),
    location: Optional[str] = Query(None, description="Filter lokasi"),
    category: Optional[str] = Query(None, description="Slug kategori"),
    start_date: Optional[str] = Query(None, description="Tanggal mulai (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Tanggal selesai (YYYY-MM-DD)"),
    event_status: Optional[str] = Query("upcoming", alias="status"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Daftar event dengan filter & pagination.
    """
    offset = (page - 1) * page_size
    events = EventService.search_events(
        query=q,
        location=location,
        category_slug=category,
        start_date=start_date,
        end_date=end_date,
        status=event_status,
        min_price=min_price,
        max_price=max_price,
        limit=page_size,
        offset=offset,
    )
    return {
        "success": True,
        "data": events,
        "page": page,
        "page_size": page_size,
        "count": len(events),
    }


@router.get("/trending")
async def trending_events(limit: int = Query(5, ge=1, le=20)):
    """Event paling banyak dilihat."""
    events = RecommendationService.get_trending_events(limit=limit)
    return {"success": True, "data": events}


@router.get("/upcoming")
async def upcoming_events(limit: int = Query(10, ge=1, le=50)):
    """Event yang akan segera berlangsung."""
    events = RecommendationService.get_upcoming_events(limit=limit)
    return {"success": True, "data": events}


@router.get("/{event_id}")
async def get_event(event_id: str):
    """Detail lengkap sebuah event."""
    event = EventService.get_event_detail(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event tidak ditemukan")
    return {"success": True, "data": event}


@router.get("/{event_id}/recommendations")
async def event_recommendations(event_id: str, limit: int = Query(3, ge=1, le=10)):
    """Rekomendasi event serupa."""
    events = RecommendationService.get_similar_events(event_id=event_id, limit=limit)
    return {"success": True, "data": events}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    body: CreateEventRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Buat event baru. Hanya untuk role `organizer` atau `admin`.
    """
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya organizer yang bisa membuat event")

    result = EventService.create_event(
        organizer_id=str(user["id"]),
        **body.dict(exclude_none=True),
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Gagal membuat event"))
    return {"success": True, "data": result.get("event")}


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    body: UpdateEventRequest,
    authorization: Optional[str] = Header(None),
):
    """Update data event. Hanya organizer pemilik event atau admin."""
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    result = EventService.update_event(event_id, **body.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Gagal update event"))
    return {"success": True, "data": result.get("event")}


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
async def delete_event(
    event_id: str,
    authorization: Optional[str] = Header(None),
):
    """Soft-delete event. Hanya organizer pemilik atau admin."""
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    result = EventService.delete_event(event_id)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Gagal menghapus event"))
    return {"success": True, "message": "Event berhasil dihapus"}


@router.get("/organizer/my-events")
async def my_events(authorization: Optional[str] = Header(None)):
    """List event yang dibuat oleh organizer yang sedang login."""
    user = _get_auth_user(authorization)
    events = EventService.get_organizer_events(organizer_id=str(user["id"]))
    return {"success": True, "data": events}
