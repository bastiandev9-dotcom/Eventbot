"""
Registrations Endpoints
=======================
Endpoint untuk booking tiket, riwayat, cancel, dan check-in.
"""

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional

from backend.services import RegistrationService
from backend.api.deps import require_auth

router = APIRouter(prefix="/registrations", tags=["Registrations"])


# ── Request Schemas ───────────────────────────────────────

class BookTicketRequest(BaseModel):
    ticket_id: str = Field(..., example="uuid-tiket")
    quantity: int = Field(default=1, ge=1, le=20)
    payment_method: Optional[str] = Field(None, example="transfer_bank")


class CheckInRequest(BaseModel):
    registration_id: str = Field(..., example="uuid-registrasi")


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

@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_ticket(
    body: BookTicketRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Pesan tiket event. User harus sudah login.
    """
    user = _get_auth_user(authorization)
    result = RegistrationService.book_ticket(
        user_id=str(user["id"]),
        ticket_id=body.ticket_id,
        quantity=body.quantity,
        payment_method=body.payment_method,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Gagal melakukan booking"),
        )
    return {
        "success": True,
        "registration_id": result["registration_id"],
        "total_price": result["total_price"],
        "message": result.get("message"),
    }


@router.get("/my")
async def my_registrations(
    reg_status: Optional[str] = Query(None, alias="status", description="Filter status: pending, confirmed, cancelled"),
    authorization: Optional[str] = Header(None),
):
    """
    Riwayat booking milik user yang sedang login.
    """
    user = _get_auth_user(authorization)
    registrations = RegistrationService.get_user_registrations(
        user_id=str(user["id"]),
        status=reg_status,
    )
    return {"success": True, "data": registrations}


@router.post("/{registration_id}/cancel")
async def cancel_registration(
    registration_id: str,
    authorization: Optional[str] = Header(None),
):
    """
    Batalkan registrasi tiket.
    """
    _get_auth_user(authorization)
    result = RegistrationService.cancel_registration(registration_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Gagal membatalkan registrasi"),
        )
    return {"success": True, "message": result["message"]}


@router.post("/{registration_id}/confirm-payment")
async def confirm_payment(
    registration_id: str,
    authorization: Optional[str] = Header(None),
):
    """
    Konfirmasi pembayaran registrasi. Hanya organizer/admin.
    """
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    result = RegistrationService.confirm_payment(registration_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal konfirmasi pembayaran",
        )
    return {"success": True, "data": result.get("registration")}


@router.post("/check-in")
async def check_in(
    body: CheckInRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Check-in peserta event. Hanya organizer/admin.
    """
    user = _get_auth_user(authorization)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    result = RegistrationService.check_in(
        registration_id=body.registration_id,
        checked_in_by=str(user["id"]),
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal check-in",
        )
    return {"success": True, "data": result.get("check_in")}
