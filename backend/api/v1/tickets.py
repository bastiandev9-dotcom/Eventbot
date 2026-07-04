"""
Tickets Endpoints
=================
Endpoint untuk manajemen tiket per event.
"""

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from backend.services import TicketService
from backend.api.deps import require_auth

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ── Request Schemas ───────────────────────────────────────

class CreateTicketRequest(BaseModel):
    event_id: str = Field(..., example="uuid-event")
    name: str = Field(..., example="Early Bird")
    description: Optional[str] = Field(None, example="Tiket harga awal, terbatas")
    price: float = Field(..., ge=0, example=150000)
    quota: int = Field(..., ge=1, example=100)
    max_per_order: int = Field(default=5, ge=1, le=20)
    sale_start: Optional[str] = Field(None, example="2026-07-01")
    sale_end: Optional[str] = Field(None, example="2026-07-31")


class UpdateTicketRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    quota: Optional[int] = Field(None, ge=1)
    max_per_order: Optional[int] = Field(None, ge=1, le=20)
    sale_start: Optional[str] = None
    sale_end: Optional[str] = None
    is_active: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────

def _get_auth_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan")
    token = authorization.split(" ", 1)[1]
    try:
        return require_auth(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ── Endpoints ─────────────────────────────────────────────

@router.get("/event/{event_id}")
async def list_tickets_by_event(event_id: str):
    """
    Ambil semua tiket yang tersedia untuk sebuah event.
    """
    tickets = TicketService.get_event_tickets(event_id)
    return {"success": True, "data": tickets}


@router.get("/{ticket_id}/availability")
async def check_availability(ticket_id: str):
    """
    Cek ketersediaan dan info harga tiket.
    """
    result = TicketService.check_availability(ticket_id)
    if result.get("message") == "Tiket tidak ditemukan":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tiket tidak ditemukan")
    return {"success": True, "data": result}


@router.get("/event/{event_id}/stats")
async def ticket_stats(
    event_id: str,
    authorization: Optional[str] = Header(None),
):
    """
    Statistik tiket per event (organizer/admin only).
    """
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    stats = TicketService.get_ticket_stats(event_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data statistik tidak ditemukan")
    return {"success": True, "data": stats}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: CreateTicketRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Buat tiket baru untuk event. Hanya organizer/admin.
    """
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya organizer yang bisa membuat tiket")

    result = TicketService.create_ticket(
        event_id=body.event_id,
        **body.dict(exclude={"event_id"}, exclude_none=True),
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message", "Gagal membuat tiket"))
    return {"success": True, "data": result.get("ticket")}


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    body: UpdateTicketRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Update data tiket. Hanya organizer/admin.
    """
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    from backend.models import TicketModel
    updated = TicketModel.update(ticket_id, **body.dict(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gagal update tiket")
    return {"success": True, "data": updated}
