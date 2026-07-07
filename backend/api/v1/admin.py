"""
Admin Endpoints
===============
Endpoint khusus admin: manajemen user, statistik, dsb.
Semua endpoint wajib role=admin.
"""

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.models.user import UserModel
from backend.config.database import execute_query
from backend.api.deps import require_auth

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Request Schemas ───────────────────────────────────────

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    role: str = Field(default="participant")
    is_active: Optional[bool] = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "User Baru",
                "email": "user@example.com",
                "password": "password123",
                "role": "participant",
                "is_active": True,
            }
        }
    }


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


# ── Helper ────────────────────────────────────────────────

def _require_admin(authorization: Optional[str]) -> dict:
    """Validasi token dan pastikan role=admin."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan")
    token = authorization.split(" ", 1)[1]
    try:
        user = require_auth(token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya admin yang dapat mengakses endpoint ini")
    return user


def _format_user(u: dict) -> dict:
    """Normalisasi field user untuk response frontend."""
    if not u:
        return {}
    return {
        "id":         str(u.get("id", "")),
        "name":       u.get("name", ""),
        "email":      u.get("email", ""),
        "role":       u.get("role", "participant"),
        "is_active":  u.get("status", "active") == "active",
        "created_at": str(u.get("created_at", "")),
        "phone":      u.get("phone"),
    }


# ── Endpoints ─────────────────────────────────────────────

@router.get("/stats")
async def get_admin_stats(
    authorization: Optional[str] = Header(None),
):
    """
    Statistik ringkasan untuk dashboard admin.
    Menggunakan stored function get_admin_dashboard_stats().
    """
    _require_admin(authorization)

    # Ambil stats dari stored function
    raw = execute_query(
        "SELECT * FROM get_admin_dashboard_stats()",
        fetch_one=True,
    ) or {}

    # Ambil event capacity samples (3 event aktif teratas)
    capacity_rows = execute_query(
        """
        SELECT e.title,
               COALESCE(r.reg_count, 0) AS registered,
               e.capacity
        FROM events e
        LEFT JOIN (
            SELECT event_id, COUNT(*) AS reg_count
            FROM registrations
            WHERE status NOT IN ('cancelled')
            GROUP BY event_id
        ) r ON r.event_id = e.id
        WHERE e.deleted_at IS NULL
          AND e.is_published = TRUE
          AND e.status IN ('upcoming', 'ongoing')
          AND e.capacity > 0
        ORDER BY e.start_date ASC
        LIMIT 5
        """,
        fetch_all=True,
    ) or []

    # Ambil distribusi event per kategori
    cat_rows = execute_query(
        """
        SELECT c.name, COUNT(DISTINCT ec.event_id) AS total
        FROM categories c
        JOIN event_categories ec ON c.id = ec.category_id
        JOIN events e ON ec.event_id = e.id
        WHERE e.deleted_at IS NULL AND e.is_published = TRUE
        GROUP BY c.name
        ORDER BY total DESC
        """,
        fetch_all=True,
    ) or []

    # Hitung registrasi & user baru minggu ini
    new_regs_week = execute_query(
        """
        SELECT COUNT(*) AS cnt FROM registrations
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
          AND status NOT IN ('cancelled')
        """,
        fetch_one=True,
    ) or {}

    new_users_week = execute_query(
        """
        SELECT COUNT(*) AS cnt FROM users
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
          AND deleted_at IS NULL
        """,
        fetch_one=True,
    ) or {}

    new_events_week = execute_query(
        """
        SELECT COUNT(*) AS cnt FROM events
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
          AND deleted_at IS NULL
        """,
        fetch_one=True,
    ) or {}

    # Hitung tiket terjual total
    tickets_sold = execute_query(
        "SELECT COALESCE(SUM(sold), 0) AS total FROM tickets WHERE deleted_at IS NULL",
        fetch_one=True,
    ) or {}

    data = {
        # Totals dari stored function
        "total_users":            int(raw.get("total_users", 0)),
        "total_events":           int(raw.get("total_events", 0)),
        "total_registrations":    int(raw.get("total_registrations", 0)),
        "total_revenue":          float(raw.get("total_revenue", 0)),
        "events_upcoming":        int(raw.get("upcoming_events", 0)),
        "events_ongoing":         int(raw.get("ongoing_events", 0)),
        "events_completed":       int(raw.get("completed_events", 0)),
        "active_users":           int(raw.get("active_users", 0)),
        "pending_registrations":  int(raw.get("pending_registrations", 0)),
        "confirmed_registrations":int(raw.get("confirmed_registrations", 0)),
        # Tiket terjual
        "tickets_sold":           int(tickets_sold.get("total", 0)),
        # Minggu ini
        "new_registrations_week": int(new_regs_week.get("cnt", 0)),
        "new_users_week":         int(new_users_week.get("cnt", 0)),
        "new_events_week":        int(new_events_week.get("cnt", 0)),
        # Capacity samples
        "capacity_samples": [
            {
                "title":      row["title"],
                "registered": int(row["registered"]),
                "capacity":   int(row["capacity"]),
            }
            for row in capacity_rows
        ],
        # Distribusi kategori
        "categories": {row["name"]: int(row["total"]) for row in cat_rows},
    }

    return {"success": True, "data": data}


# ── Mapping key settings frontend → system_settings DB ───
# Frontend Pengaturan.py menggunakan key-key ini dalam payload PUT
_SETTINGS_KEY_MAP: Dict[str, str] = {
    # Personality
    "bot_name":              "chatbot_name",
    "bot_emoji":             "chatbot_emoji",
    "personality":           "chatbot_personality",
    "language":              "chatbot_language",
    "tagline":               "chatbot_tagline",
    # Messages
    "welcome_message":       "chatbot_greeting",
    "fallback_message":      "chatbot_fallback",
    "farewell_message":      "chatbot_farewell",
    "error_message":         "chatbot_error",
    "default_quick_replies": "chatbot_quick_replies",
    # Behavior
    "max_history":             "max_chat_history",
    "typing_delay_ms":         "chatbot_typing_delay",
    "enable_suggestions":      "chatbot_enable_suggestions",
    "enable_event_cards":      "chatbot_enable_event_cards",
    "enable_typing_animation": "chatbot_enable_typing_animation",
    "max_events_in_chat":      "chatbot_max_events",
}

_SETTINGS_DEFAULTS: Dict[str, Any] = {
    "bot_name":               "EventBot",
    "bot_emoji":              "🤖",
    "personality":            "Ramah & Casual",
    "language":               "Bahasa Indonesia",
    "tagline":                "Asisten cerdas untuk manajemen event",
    "welcome_message":        "Halo! 👋 Saya EventBot, ada yang bisa saya bantu?",
    "fallback_message":       "Maaf, saya belum mengerti. Ketik 'bantuan'.",
    "farewell_message":       "Terima kasih! Sampai jumpa! 👋",
    "error_message":          "Terjadi kesalahan. Coba lagi!",
    "default_quick_replies":  ["Ada event apa?", "Event gratis", "Bantuan"],
    "max_history":            50,
    "typing_delay_ms":        800,
    "enable_suggestions":     True,
    "enable_event_cards":     True,
    "enable_typing_animation":True,
    "max_events_in_chat":     3,
}


@router.get("/settings")
async def get_settings(
    authorization: Optional[str] = Header(None),
):
    """Ambil semua pengaturan chatbot (admin only)."""
    _require_admin(authorization)

    import json
    all_rows = SystemSettingsModel.get_all()
    db_map = {row["key"]: row["value"] for row in all_rows}

    data: Dict[str, Any] = {}
    for frontend_key, db_key in _SETTINGS_KEY_MAP.items():
        raw = db_map.get(db_key)
        default = _SETTINGS_DEFAULTS.get(frontend_key)

        if raw is None:
            data[frontend_key] = default
            continue

        # Konversi tipe
        if isinstance(default, bool):
            data[frontend_key] = raw.lower() in ("true", "1", "yes")
        elif isinstance(default, int):
            try:
                data[frontend_key] = int(raw)
            except (ValueError, TypeError):
                data[frontend_key] = default
        elif isinstance(default, list):
            try:
                data[frontend_key] = json.loads(raw)
            except Exception:
                data[frontend_key] = [s.strip() for s in raw.split(",") if s.strip()]
        else:
            data[frontend_key] = raw

    return {"success": True, "data": data}


@router.put("/settings")
async def update_settings(
    body: Dict[str, Any],
    authorization: Optional[str] = Header(None),
):
    """Update pengaturan chatbot (admin only). Body: {frontend_key: value}."""
    _require_admin(authorization)

    import json
    updated_keys = []
    for frontend_key, value in body.items():
        db_key = _SETTINGS_KEY_MAP.get(frontend_key)
        if not db_key:
            continue  # Abaikan key yang tidak dikenal
        # Serialisasi value ke string
        if isinstance(value, (list, dict)):
            str_value = json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            str_value = "true" if value else "false"
        else:
            str_value = str(value)
        SystemSettingsModel.set(db_key, str_value)
        updated_keys.append(frontend_key)

    return {
        "success": True,
        "message": f"{len(updated_keys)} pengaturan berhasil disimpan",
        "updated": updated_keys,
    }


@router.get("/users")
async def list_users(
    role: Optional[str] = Query(None, description="Filter role: admin, participant"),
    user_status: Optional[str] = Query(None, alias="status", description="Filter status: active, inactive"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    authorization: Optional[str] = Header(None),
):
    """Daftar semua user (admin only)."""
    _require_admin(authorization)

    offset = (page - 1) * page_size
    users = UserModel.list_all(role=role, status=user_status, limit=page_size, offset=offset)
    total = UserModel.count(role=role, status=user_status)

    return {
        "success":    True,
        "data":       [_format_user(u) for u in users],
        "count":      total,
        "page":       page,
        "page_size":  page_size,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    """Detail satu user (admin only)."""
    _require_admin(authorization)
    user = UserModel.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
    return {"success": True, "data": _format_user(user)}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    authorization: Optional[str] = Header(None),
):
    """Tambah user baru (admin only)."""
    _require_admin(authorization)

    new_user = UserModel.create(
        name=body.name,
        email=body.email,
        password=body.password,
        role=body.role,
    )
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gagal membuat user. Email mungkin sudah digunakan.")

    # Set status sesuai is_active
    if not body.is_active:
        UserModel.update(str(new_user["id"]), status="inactive")
        new_user["status"] = "inactive"

    return {"success": True, "data": _format_user(new_user), "message": "User berhasil dibuat"}


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    authorization: Optional[str] = Header(None),
):
    """Update data user (admin only)."""
    _require_admin(authorization)

    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.email is not None:
        updates["email"] = body.email
    if body.role is not None:
        updates["role"] = body.role
    if body.is_active is not None:
        updates["status"] = "active" if body.is_active else "inactive"

    updated = None
    if updates:
        updated = UserModel.update(user_id, **updates)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    # Update password terpisah jika ada
    if body.password:
        UserModel.update_password(user_id, body.password)

    # Ambil data terbaru
    final = UserModel.get_by_id(user_id)
    return {"success": True, "data": _format_user(final), "message": "User berhasil diperbarui"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    """Hapus (soft-delete) user (admin only)."""
    admin = _require_admin(authorization)

    # Cegah admin hapus dirinya sendiri
    if str(admin.get("id")) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak bisa menghapus akun sendiri")

    deleted = UserModel.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    return {"success": True, "message": "User berhasil dihapus"}
