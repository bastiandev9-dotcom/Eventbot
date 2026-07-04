"""
Test Chatbot Endpoints & NLP Logic
====================================
Unit test untuk endpoint /api/v1/chatbot/* dan regex NLP.
"""

import pytest
from unittest.mock import patch, MagicMock


# ── NLP Unit Tests ────────────────────────────────────────

class TestIntentDetection:
    """Test match_intent() dengan berbagai kalimat."""

    def test_sapaan(self):
        from backend.nlp.regex_rules import match_intent
        for kalimat in ["halo", "hai bot", "hey", "selamat pagi"]:
            assert match_intent(kalimat) == "sapaan", f"Gagal untuk: '{kalimat}'"

    def test_bantuan(self):
        from backend.nlp.regex_rules import match_intent
        for kalimat in ["bantuan", "minta tolong", "fitur apa saja", "help"]:
            assert match_intent(kalimat) == "tanya_bantuan", f"Gagal untuk: '{kalimat}'"

    def test_cari_event(self):
        from backend.nlp.regex_rules import match_intent
        for kalimat in [
            "cari event teknologi",
            "ada event apa saja",
            "daftar acara bulan ini",
        ]:
            assert match_intent(kalimat) == "cari_event", f"Gagal untuk: '{kalimat}'"

    def test_detail_event(self):
        from backend.nlp.regex_rules import match_intent
        for kalimat in [
            "detail event Tech Conference",
            "info acara besok",
            "harga tiket event X",
        ]:
            assert match_intent(kalimat) == "detail_event", f"Gagal untuk: '{kalimat}'"

    def test_daftar_tiket(self):
        from backend.nlp.regex_rules import match_intent
        for kalimat in ["daftar event", "pesan tiket", "booking acara", "mau ikut event"]:
            assert match_intent(kalimat) == "daftar_tiket", f"Gagal untuk: '{kalimat}'"

    def test_lihat_jadwal(self):
        from backend.nlp.regex_rules import match_intent
        assert match_intent("jadwal saya") == "lihat_jadwal"
        assert match_intent("event saya") == "lihat_jadwal"

    def test_keluar(self):
        from backend.nlp.regex_rules import match_intent
        for kalimat in ["bye", "dadah", "terima kasih", "sampai jumpa"]:
            assert match_intent(kalimat) == "keluar", f"Gagal untuk: '{kalimat}'"

    def test_tidak_dikenal(self):
        from backend.nlp.regex_rules import match_intent
        assert match_intent("xyzqwerty") == "tidak_dikenal"
        assert match_intent("123 456") == "tidak_dikenal"


class TestEntityExtraction:
    """Test extract_entities() untuk location, date, category."""

    def test_extract_location(self):
        from backend.nlp.regex_rules import extract_entities
        entities = extract_entities("ada event di Jakarta minggu ini")
        assert "location" in entities
        locations = [loc.lower() for loc in entities["location"]]
        assert any("jakarta" in loc for loc in locations)

    def test_extract_date(self):
        from backend.nlp.regex_rules import extract_entities
        entities = extract_entities("event bulan Agustus 2026")
        assert "date" in entities

    def test_extract_category_tech(self):
        from backend.nlp.regex_rules import extract_entities
        entities = extract_entities("cari event teknologi di Bandung")
        assert "category" in entities

    def test_no_entities(self):
        from backend.nlp.regex_rules import extract_entities
        entities = extract_entities("halo")
        assert isinstance(entities, dict)


# ── Chatbot REST Endpoint ─────────────────────────────────

class TestChatbotMessage:

    def test_send_message_success(self, client):
        """POST /chatbot/message harus return response dari bot."""
        mock_result = {
            "response": "Halo! Ada yang bisa saya bantu?",
            "intent": "sapaan",
            "entities": {},
            "session_token": "tok_abc123",
            "quick_replies": ["🔍 Cari Event", "❓ Bantuan"],
        }
        with patch("backend.api.v1.chatbot._chatbot_service.process_message") as mock_proc:
            mock_proc.return_value = mock_result
            resp = client.post("/api/v1/chatbot/message", json={"message": "halo"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "response" in data["data"]
        assert "session_token" in data["data"]

    def test_send_message_with_session(self, client):
        """Request dengan session_token harus meneruskannya ke service."""
        mock_result = {
            "response": "Lanjut percakapan sebelumnya.",
            "intent": "cari_event",
            "entities": {},
            "session_token": "tok_existing",
            "quick_replies": [],
        }
        with patch("backend.api.v1.chatbot._chatbot_service.process_message") as mock_proc:
            mock_proc.return_value = mock_result
            resp = client.post("/api/v1/chatbot/message", json={
                "message": "cari event",
                "session_token": "tok_existing",
            })
        assert resp.status_code == 200
        mock_proc.assert_called_once_with(
            message="cari event",
            session_token="tok_existing",
            user_id=None,
        )

    def test_send_empty_message(self, client):
        """Pesan kosong harus return 422 (validasi Pydantic)."""
        resp = client.post("/api/v1/chatbot/message", json={"message": ""})
        assert resp.status_code == 422

    def test_send_message_no_body(self, client):
        """Request tanpa body harus return 422."""
        resp = client.post("/api/v1/chatbot/message")
        assert resp.status_code == 422


class TestChatbotHistory:

    def test_get_history_success(self, client):
        """GET /chatbot/history dengan session_token valid harus return list."""
        mock_history = [
            {"role": "user", "content": "halo", "created_at": "2026-07-04T00:00:00"},
            {"role": "assistant", "content": "Halo! Ada yang bisa saya bantu?", "created_at": "2026-07-04T00:00:01"},
        ]
        with patch("backend.api.v1.chatbot._chatbot_service.get_chat_history") as mock_hist:
            mock_hist.return_value = mock_history
            resp = client.get("/api/v1/chatbot/history?session_token=tok_abc123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2

    def test_get_history_missing_token(self, client):
        """GET /chatbot/history tanpa session_token harus return 422."""
        resp = client.get("/api/v1/chatbot/history")
        assert resp.status_code == 422


class TestChatbotIntents:

    def test_list_intents(self, client):
        """GET /chatbot/intents harus return daftar intent."""
        resp = client.get("/api/v1/chatbot/intents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        intents = data["data"]
        # Intent wajib ada
        assert "sapaan" in intents
        assert "cari_event" in intents
        assert "daftar_tiket" in intents


# ── ChatbotService Unit Test ──────────────────────────────

class TestChatbotService:

    def test_process_message_sapaan(self):
        """Service harus mendeteksi intent sapaan dan return greeting."""
        with patch("backend.models.ChatSessionModel.get_by_token", return_value=None), \
             patch("backend.models.ChatSessionModel.create", return_value={
                 "id": "session-001",
                 "session_token": "tok_new",
             }), \
             patch("backend.models.ChatMessageModel.create"), \
             patch("backend.nlp.context_manager.ContextManager.get_context", return_value={}), \
             patch("backend.nlp.context_manager.ContextManager.update_context"):
            from backend.services.chatbot_service import ChatbotService
            svc = ChatbotService()
            result = svc.process_message("halo")

        assert "response" in result
        assert result["intent"] == "sapaan"
        assert "session_token" in result

    def test_process_message_tidak_dikenal(self):
        """Pesan tidak dikenal harus menggunakan fallback."""
        with patch("backend.models.ChatSessionModel.get_by_token", return_value=None), \
             patch("backend.models.ChatSessionModel.create", return_value={
                 "id": "session-002",
                 "session_token": "tok_new2",
             }), \
             patch("backend.models.ChatMessageModel.create"), \
             patch("backend.nlp.context_manager.ContextManager.get_context", return_value={}), \
             patch("backend.nlp.context_manager.ContextManager.update_context"), \
             patch("backend.models.KnowledgeBaseModel.search", return_value=[]):
            from backend.services.chatbot_service import ChatbotService
            svc = ChatbotService()
            result = svc.process_message("xyzqwerty123")

        assert result["intent"] == "tidak_dikenal"
        assert len(result["response"]) > 0
