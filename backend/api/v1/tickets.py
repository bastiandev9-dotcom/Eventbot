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
    event_id: str
    name: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    quota: int = Field(default=0, ge=0)       # alias untuk quantity
    quantity: Optional[int] = Field(None, ge=0)  # alternatif dari quota
    max_per_order: int = Field(default=5, ge=1, le=20)
    sale_start: Optional[str] = None           # alias untuk sale_starts_at
    sale_end: Optional[str] = None             # alias untuk sale_ends_at
    sale_starts_at: Optional[str] = None
    sale_ends_at: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "uuid-event",
                "name": "Early Bird",
                "description": "Tiket harga awal, terbatas",
                "price": 150000,
                "quota": 100,
                "sale_start": "2026-07-01",
                "sale_end": "2026-07-31",
            }
        }
    }


class UpdateTicketRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    quota: Optional[int] = Field(None, ge=0)       # alias untuk quantity
    quantity: Optional[int] = Field(None, ge=0)
    max_per_order: Optional[int] = Field(None, ge=1, le=20)
    sale_start: Optional[str] = None               # alias untuk sale_starts_at
    sale_end: Optional[str] = None                 # alias untuk sale_ends_at
    sale_starts_at: Optional[str] = None
    sale_ends_at: Optional[str] = None
    status: Optional[str] = None
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

@router.get("/")
async def list_tickets(
    event_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    """
    Ambil semua tiket. Filter opsional per event_id.
    Endpoint ini dipanggil dari halaman Manajemen Tiket (admin).
    """
    from backend.models.ticket import TicketModel
    if event_id:
        tickets = TicketModel.get_by_event(event_id)
    else:
        tickets = TicketModel.get_all()
    return {"success": True, "data": tickets}


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
    Statistik tiket per event (admin only).
    """
    user = _get_auth_user(authorization)
    if user.get("role") != "admin":
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
    Buat tiket baru untuk event. Hanya admin.
    """
    user = _get_auth_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya admin yang bisa membuat tiket")

    # Normalisasi field: quota → quantity, sale_start → sale_starts_at, sale_end → sale_ends_at
    quantity = body.quantity if body.quantity is not None else body.quota

    result = TicketService.create_ticket(
        event_id=body.event_id,
        name=body.name,
        price=body.price,
        quantity=quantity,
        description=body.description,
        max_per_order=body.max_per_order,
        sale_starts_at=body.sale_starts_at or body.sale_start,
        sale_ends_at=body.sale_ends_at or body.sale_end,
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
    Update data tiket. Hanya admin.
    """
    user = _get_auth_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    from backend.models import TicketModel

    # Normalisasi field: quota → quantity, sale_start → sale_starts_at, sale_end → sale_ends_at
    update_data = body.model_dump(exclude_none=True)

    if "quota" in update_data and "quantity" not in update_data:
        update_data["quantity"] = update_data.pop("quota")
    else:
        update_data.pop("quota", None)

    if "sale_start" in update_data and "sale_starts_at" not in update_data:
        update_data["sale_starts_at"] = update_data.pop("sale_start")
    else:
        update_data.pop("sale_start", None)

    if "sale_end" in update_data and "sale_ends_at" not in update_data:
        update_data["sale_ends_at"] = update_data.pop("sale_end")
    else:
        update_data.pop("sale_end", None)

    update_data.pop("is_active", None)  # field ini tidak ada di model

    # Validasi: quantity tidak boleh lebih kecil dari sold
    if "quantity" in update_data:
        from backend.models.ticket import TicketModel as TM
        current = TM.get_by_id(ticket_id)
        if current:
            sold = current.get("sold_count") or current.get("sold", 0)
            if update_data["quantity"] < sold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Kuota tidak boleh kurang dari tiket terjual ({sold} terjual). Minimal kuota: {sold}."
                )

    updated = TicketModel.update(ticket_id, **update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gagal update tiket")
    return {"success": True, "data": updated}



@router.delete("/{ticket_id}", status_code=status.HTTP_200_OK)
async def delete_ticket(
    ticket_id: str,
    authorization: Optional[str] = Header(None),
):
    """
    Hapus (soft delete) tiket. Hanya admin.
    Tiket yang sudah ada pembelian tidak bisa dihapus.
    """
    user = _get_auth_user(authorization)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    from backend.models.ticket import TicketModel
    # Cek apakah ada registrasi aktif untuk tiket ini
    from backend.config import execute_query
    active_regs = execute_query(
        "SELECT COUNT(*) AS cnt FROM registrations WHERE ticket_id = %s AND status != 'cancelled'",
        (ticket_id,), fetch_one=True
    )
    if active_regs and active_regs["cnt"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tiket tidak bisa dihapus — masih ada {active_regs['cnt']} registrasi aktif."
        )

    success = TicketModel.delete(ticket_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tiket tidak ditemukan")
    return {"success": True, "message": "Tiket berhasil dihapus"}
