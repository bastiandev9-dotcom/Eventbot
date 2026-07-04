"""
WebSocket Endpoint
==================
Real-time chat via WebSocket untuk EventBot.

URL: ws://host/ws/chat/{session_token}

Protocol:
  Client kirim: JSON {"message": "...", "user_id": "..." (opsional)}
  Server balas: JSON {"response": "...", "intent": "...", "entities": {...},
                      "session_token": "...", "quick_replies": [...]}
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services import ChatbotService

websocket_router = APIRouter(tags=["WebSocket"])

# Shared chatbot service instance
_chatbot_service = ChatbotService()


class ConnectionManager:
    """Mengelola koneksi WebSocket yang aktif."""

    def __init__(self):
        # { session_token: WebSocket }
        self._active: dict[str, WebSocket] = {}

    async def connect(self, session_token: str, websocket: WebSocket):
        await websocket.accept()
        self._active[session_token] = websocket

    def disconnect(self, session_token: str):
        self._active.pop(session_token, None)

    async def send(self, session_token: str, data: dict):
        ws = self._active.get(session_token)
        if ws:
            await ws.send_text(json.dumps(data, ensure_ascii=False))


manager = ConnectionManager()


@websocket_router.websocket("/ws/chat/{session_token}")
async def websocket_chat(websocket: WebSocket, session_token: str):
    """
    WebSocket endpoint untuk chatbot real-time.

    - **session_token**: Gunakan `"new"` untuk membuat sesi baru,
      atau token sesi yang sudah ada untuk lanjut percakapan.
    """
    # Normalise token baru
    if session_token == "new":
        session_token = None

    await manager.connect(session_token or "pending", websocket)

    try:
        while True:
            raw = await websocket.receive_text()

            # Parse pesan
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                # Treat sebagai plain text
                payload = {"message": raw}

            message: str = payload.get("message", "").strip()
            user_id: str | None = payload.get("user_id")

            if not message:
                await websocket.send_text(
                    json.dumps({"error": "Pesan tidak boleh kosong"}, ensure_ascii=False)
                )
                continue

            # Proses oleh chatbot
            result = _chatbot_service.process_message(
                message=message,
                session_token=session_token,
                user_id=user_id,
            )

            # Update session token dari result (bisa berubah saat baru)
            session_token = result.get("session_token", session_token)

            await websocket.send_text(
                json.dumps({"success": True, "data": result}, ensure_ascii=False)
            )

    except WebSocketDisconnect:
        manager.disconnect(session_token or "pending")
    except Exception as e:
        # Kirim error ke client lalu tutup
        try:
            await websocket.send_text(
                json.dumps({"error": f"Internal error: {str(e)}"}, ensure_ascii=False)
            )
        except Exception:
            pass
        manager.disconnect(session_token or "pending")
