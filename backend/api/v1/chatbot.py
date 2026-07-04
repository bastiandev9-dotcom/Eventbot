"""
Chatbot Endpoints
=================
Endpoint REST untuk interaksi dengan chatbot NLP EventBot.
"""

from fastapi import APIRouter, Header, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from backend.services import ChatbotService
from backend.api.deps import get_current_user

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Instance service (reuse antar request)
_chatbot_service = ChatbotService()


# ── Request Schemas ───────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, example="Ada event teknologi di Jakarta?")
    session_token: Optional[str] = Field(None, example="tok_abc123")


# ── Helpers ───────────────────────────────────────────────

def _extract_user_id(authorization: Optional[str]) -> Optional[str]:
    """Ambil user_id jika user login, kembalikan None jika guest."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    return str(user["id"]) if user else None


# ── Endpoints ─────────────────────────────────────────────

@router.post("/message")
async def send_message(
    body: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Kirim pesan ke chatbot dan terima respons NLP.

    - **message**: Teks pesan user
    - **session_token**: Token sesi sebelumnya (opsional, untuk lanjut percakapan)

    Response berisi:
    - `response`: Teks balasan bot
    - `intent`: Intent yang terdeteksi
    - `entities`: Entity yang diekstrak
    - `session_token`: Token sesi (simpan untuk request berikutnya)
    - `quick_replies`: Pilihan cepat yang disarankan
    """
    user_id = _extract_user_id(authorization)

    result = _chatbot_service.process_message(
        message=body.message,
        session_token=body.session_token,
        user_id=user_id,
    )
    return {"success": True, "data": result}


@router.get("/history")
async def chat_history(
    session_token: str = Query(..., description="Token sesi chatbot"),
):
    """
    Ambil history percakapan berdasarkan session token.
    """
    if not session_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="session_token wajib diisi")

    history = _chatbot_service.get_chat_history(session_token)
    return {"success": True, "data": history}


@router.get("/intents")
async def list_intents():
    """
    Daftar intent yang didukung chatbot beserta contoh kalimat.
    """
    from backend.nlp.regex_rules import INTENT_RULES
    intents = {
        "sapaan": "Halo, Hi, Assalamualaikum",
        "tanya_bantuan": "Bantuan, menu, fitur apa",
        "cari_event": "Cari event teknologi, ada event apa saja",
        "detail_event": "Info event X, detail acara Y",
        "daftar_tiket": "Daftar event, pesan tiket, booking",
        "lihat_jadwal": "Jadwal saya, event terdaftar",
        "profil": "Profil saya, akun",
        "keluar": "Bye, terima kasih, keluar",
    }
    return {"success": True, "data": intents}
