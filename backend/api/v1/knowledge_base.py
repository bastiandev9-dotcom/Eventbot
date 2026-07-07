"""
Knowledge Base Endpoints
========================
Endpoint untuk manajemen FAQ chatbot, intents, dan response templates.
Semua endpoint wajib role=admin.
"""

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.models.knowledge_base import KnowledgeBaseModel
from backend.models.system_settings import SystemSettingsModel
from backend.api.deps import require_auth

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


# ── Request Schemas ───────────────────────────────────────

class FAQCreateRequest(BaseModel):
    question: str = Field(..., min_length=5)
    answer: str   = Field(..., min_length=5)
    category: Optional[str] = "general"
    keywords: Optional[List[str]] = []
    priority: Optional[int] = 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "Bagaimana cara mendaftar event?",
                "answer":   "Buka Event Explorer, pilih event, klik Daftar.",
                "category": "event",
                "keywords": ["daftar", "register", "cara"],
                "priority": 5,
            }
        }
    }


class FAQUpdateRequest(BaseModel):
    question:  Optional[str] = None
    answer:    Optional[str] = None
    category:  Optional[str] = None
    keywords:  Optional[List[str]] = None
    priority:  Optional[int] = None
    is_active: Optional[bool] = None


class TemplateUpdateRequest(BaseModel):
    template: str = Field(..., min_length=1)


# ── Helper ────────────────────────────────────────────────

def _require_admin(authorization: Optional[str]) -> dict:
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


def _serialize_faq(row: dict) -> dict:
    """Normalisasi field FAQ untuk response."""
    if not row:
        return {}
    return {
        "id":        str(row.get("id", "")),
        "question":  row.get("question", ""),
        "answer":    row.get("answer", ""),
        "category":  row.get("category", "general"),
        "keywords":  row.get("keywords") or [],
        "priority":  row.get("priority", 0),
        "is_active": row.get("is_active", True),
    }


# ── FAQ Endpoints ─────────────────────────────────────────

@router.get("/faq")
async def list_faq(
    category: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    """Ambil semua FAQ (admin only)."""
    _require_admin(authorization)
    faqs = KnowledgeBaseModel.list_all(category=category, active_only=False)
    return {"success": True, "data": [_serialize_faq(f) for f in faqs]}


@router.post("/faq", status_code=status.HTTP_201_CREATED)
async def create_faq(
    body: FAQCreateRequest,
    authorization: Optional[str] = Header(None),
):
    """Tambah FAQ baru (admin only)."""
    _require_admin(authorization)
    faq = KnowledgeBaseModel.create(
        category=body.category or "general",
        question=body.question,
        answer=body.answer,
        keywords=body.keywords or [],
        priority=body.priority or 0,
    )
    if not faq:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gagal membuat FAQ")
    return {"success": True, "data": _serialize_faq(faq), "message": "FAQ berhasil ditambahkan"}


@router.put("/faq/{faq_id}")
async def update_faq(
    faq_id: str,
    body: FAQUpdateRequest,
    authorization: Optional[str] = Header(None),
):
    """Update FAQ (admin only)."""
    _require_admin(authorization)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data yang diubah")
    updated = KnowledgeBaseModel.update(faq_id, **updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ tidak ditemukan")
    return {"success": True, "data": updated, "message": "FAQ berhasil diperbarui"}


@router.delete("/faq/{faq_id}")
async def delete_faq(
    faq_id: str,
    authorization: Optional[str] = Header(None),
):
    """Hapus FAQ (admin only)."""
    _require_admin(authorization)
    deleted = KnowledgeBaseModel.delete(faq_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ tidak ditemukan")
    return {"success": True, "message": "FAQ berhasil dihapus"}


# ── Intents Endpoint ──────────────────────────────────────

@router.get("/intents")
async def list_intents(
    authorization: Optional[str] = Header(None),
):
    """
    Ambil daftar intent & contoh kalimat dari regex_rules.py (read-only).
    Admin only.
    """
    _require_admin(authorization)

    try:
        from backend.nlp.regex_rules import INTENT_RULES
        data = {}
        for intent_name, patterns in INTENT_RULES.items():
            # Buat contoh kalimat dari pattern (ambil keyword utama)
            import re
            examples = []
            for pattern in patterns[:2]:
                # Ekstrak kata-kata dari pattern sebagai contoh
                words = re.findall(r'[a-zA-Z_\s]+', pattern)
                cleaned = " ".join(w.strip() for w in words if len(w.strip()) > 2)
                if cleaned:
                    examples.append(cleaned[:60])

            data[intent_name] = {
                "description": _intent_descriptions().get(intent_name, intent_name.replace("_", " ").title()),
                "examples":    examples[:5],
                "pattern_count": len(patterns),
            }
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Gagal memuat intents: {e}")


def _intent_descriptions() -> dict:
    return {
        "sapaan":        "Salam pembuka dari user",
        "tanya_bantuan": "User meminta bantuan atau panduan",
        "daftar_tiket":  "User ingin memesan atau membeli tiket",
        "detail_event":  "User ingin melihat detail sebuah event",
        "cari_event":    "User ingin mencari event berdasarkan kriteria",
        "lihat_jadwal":  "User ingin melihat jadwal atau tiket yang dimiliki",
        "profil":        "User ingin melihat atau mengubah profilnya",
        "keluar":        "User mengakhiri percakapan",
    }


# ── Templates Endpoints ───────────────────────────────────

# Key-key template yang disimpan di system_settings
_TEMPLATE_KEYS = [
    "chatbot_greeting",
    "chatbot_fallback",
    "chatbot_farewell",
    "chatbot_error",
]

_TEMPLATE_DEFAULTS = {
    "chatbot_greeting": "Halo! 👋 Saya EventBot, ada yang bisa saya bantu?",
    "chatbot_fallback": "Maaf, saya tidak mengerti. Ketik 'bantuan' untuk melihat fitur.",
    "chatbot_farewell": "Terima kasih! Sampai jumpa! 👋",
    "chatbot_error":    "Terjadi kesalahan. Silakan coba lagi.",
}


@router.get("/templates")
async def list_templates(
    authorization: Optional[str] = Header(None),
):
    """Ambil response templates chatbot dari system_settings (admin only)."""
    _require_admin(authorization)

    all_settings = SystemSettingsModel.get_all()
    settings_map = {row["key"]: row["value"] for row in all_settings}

    templates = {}
    for key in _TEMPLATE_KEYS:
        templates[key] = settings_map.get(key, _TEMPLATE_DEFAULTS.get(key, ""))

    return {"success": True, "data": templates}


@router.put("/templates/{template_key}")
async def update_template(
    template_key: str,
    body: TemplateUpdateRequest,
    authorization: Optional[str] = Header(None),
):
    """Update satu response template (admin only)."""
    _require_admin(authorization)

    if template_key not in _TEMPLATE_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template key tidak valid. Pilihan: {', '.join(_TEMPLATE_KEYS)}"
        )

    SystemSettingsModel.set(template_key, body.template)
    return {"success": True, "message": f"Template '{template_key}' berhasil diperbarui"}
