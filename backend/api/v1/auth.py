"""
Auth Endpoints
==============
Endpoint untuk register, login, logout, dan profil user.
"""

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from backend.services import AuthService
from backend.api.deps import get_current_user, require_auth

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Request / Response Schemas ────────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="participant")
    phone: Optional[str] = None
    bio: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Budi Santoso",
                "email": "budi@email.com",
                "password": "secret123",
                "role": "participant",
                "phone": "08123456789",
                "bio": "Suka ikut event teknologi",
            }
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "budi@email.com",
                "password": "secret123",
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


# ── Endpoints ─────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """
    Daftarkan akun baru.

    - **name**: Nama lengkap user
    - **email**: Email unik
    - **password**: Minimal 6 karakter
    - **role**: `participant` (default)
    """
    result = AuthService.register(
        name=body.name,
        email=body.email,
        password=body.password,
        role=body.role,
        phone=body.phone,
        bio=body.bio,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Registrasi gagal"),
        )
    return {
        "success": True,
        "message": result["message"],
        "user": result.get("user"),
    }


@router.post("/login")
async def login(body: LoginRequest):
    """
    Login dengan email & password, kembalikan JWT access token.
    """
    result = AuthService.login(email=body.email, password=body.password)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("message", "Login gagal"),
        )
    return {
        "success": True,
        "access_token": result["access_token"],
        "token_type": "bearer",
        "user": result.get("user"),
    }


@router.get("/me")
async def get_profile(authorization: Optional[str] = Header(None)):
    """
    Ambil data profil user yang sedang login.
    Butuh header: `Authorization: Bearer <token>`
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak ditemukan",
        )
    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa",
        )
    # Hilangkan password_hash dari response
    user.pop("password_hash", None)
    return {"success": True, "user": user}


@router.put("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Ganti password user yang sedang login.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan")

    token = authorization.split(" ", 1)[1]
    try:
        user = require_auth(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    result = AuthService.change_password(
        user_id=str(user["id"]),
        old_password=body.old_password,
        new_password=body.new_password,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Gagal mengganti password"),
        )
    return {"success": True, "message": result["message"]}


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Logout — pada JWT stateless cukup balas 200.
    Client harus menghapus token dari storage.
    """
    return {"success": True, "message": "Logout berhasil. Silakan hapus token di sisi client."}
