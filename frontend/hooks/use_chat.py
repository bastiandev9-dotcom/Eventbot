"""
use_chat Hook
=============
Hook untuk manajemen state chat dengan EventBot.
Mengelola pengiriman pesan, history percakapan, dan session token chatbot.
"""

import streamlit as st
import time
from typing import Optional, List, Dict, Any, Tuple

from utils.session_manager import SessionManager
from utils.api_client import APIClient, APIError


def use_chat() -> Dict[str, Any]:
    """
    Hook untuk interaksi chatbot EventBot.

    Returns:
        Dict berisi:
        - messages: list pesan history
        - is_typing: bool (simulasi typing indicator)
        - send_message(text) -> (success, bot_response)
        - clear_history() -> None
        - load_history_from_backend() -> bool
    """
    SessionManager.init()

    def send_message(text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Kirim pesan ke chatbot backend.

        Alur:
        1. Tambah pesan user ke history lokal
        2. Set is_typing = True
        3. Kirim ke /chatbot/message
        4. Simpan respons dan session_token
        5. Tambah respons bot ke history

        Args:
            text: Teks pesan dari user

        Returns:
            (success, bot_response_dict) atau (False, None) jika error
        """
        if not text or not text.strip():
            return False, None

        # Simpan pesan user ke history lokal
        SessionManager.add_chat_message(role="user", content=text.strip())

        # Set typing indicator
        st.session_state["chat_is_typing"] = True

        token = SessionManager.get_token()
        client = APIClient(token=token)
        session_token = SessionManager.get_chat_session()

        try:
            result = client.send_message(
                message=text.strip(),
                session_token=session_token,
            )

            data = result.get("data", {})

            # Update session token chatbot
            new_session_token = data.get("session_token")
            if new_session_token:
                SessionManager.set_chat_session(new_session_token)

            # Simpan respons bot ke history
            bot_response = data.get("response", "Maaf, saya tidak mengerti.")
            quick_replies = data.get("quick_replies", [])
            event_cards = data.get("events", [])

            SessionManager.add_chat_message(
                role="bot",
                content=bot_response,
                extra={
                    "quick_replies": quick_replies,
                    "event_cards": event_cards,
                    "intent": data.get("intent"),
                },
            )

            st.session_state["chat_is_typing"] = False
            return True, data

        except APIError as e:
            # Tampilkan error sebagai pesan bot
            error_msg = (
                "Maaf, tidak dapat terhubung ke server. "
                "Pastikan backend EventBot sudah berjalan. 🔌"
                if e.status_code == 0
                else f"Error: {e.message}"
            )
            SessionManager.add_chat_message(role="bot", content=error_msg)
            st.session_state["chat_is_typing"] = False
            return False, None

        except Exception:
            SessionManager.add_chat_message(
                role="bot",
                content="Maaf, terjadi kesalahan. Coba lagi. 🔄",
            )
            st.session_state["chat_is_typing"] = False
            return False, None

    def clear_history() -> None:
        """Reset seluruh percakapan."""
        SessionManager.clear_chat_history()
        st.session_state["chat_is_typing"] = False

    def load_history_from_backend() -> bool:
        """
        Muat history percakapan dari backend berdasarkan session token.
        Berguna ketika user refresh halaman dan token masih ada.

        Returns:
            True jika berhasil, False jika gagal/tidak ada history.
        """
        session_token = SessionManager.get_chat_session()
        if not session_token:
            return False

        token = SessionManager.get_token()
        client = APIClient(token=token)

        try:
            result = client.get_chat_history(session_token=session_token)
            history = result.get("data", [])
            if history:
                # Set history ke session state (jangan duplikat)
                current_history = SessionManager.get_chat_history()
                if not current_history:
                    st.session_state[SessionManager.KEY_CHAT_HISTORY] = [
                        {
                            "role": msg.get("role", "user"),
                            "content": msg.get("message", ""),
                        }
                        for msg in history
                    ]
                return True
            return False
        except Exception:
            return False

    def get_suggested_questions() -> List[str]:
        """
        Kembalikan daftar pertanyaan saran untuk new chat.
        Ini adalah quick start prompts di awal percakapan.
        """
        return []  # Quick replies dihapus sesuai permintaan user

    def get_typing_placeholder() -> str:
        """Kembalikan teks animasi typing indicator."""
        return "EventBot sedang mengetik..."

    def is_typing() -> bool:
        return bool(st.session_state.get("chat_is_typing", False))

    def get_welcome_message() -> Dict[str, Any]:
        """Kembalikan pesan selamat datang default dari bot."""
        return {
            "role": "bot",
            "content": (
                "Halo! 👋 Saya **EventBot**, asisten cerdas untuk membantu kamu "
                "menemukan dan mendaftar event seru! 🎉\n\n"
                "Kamu bisa tanya saya tentang:\n"
                "- 🔍 Mencari event berdasarkan topik atau lokasi\n"
                "- 🎫 Informasi tiket dan pendaftaran\n"
                "- 📅 Jadwal event yang akan datang\n\n"
                "Mau tanya apa? 😊"
            ),
            "quick_replies": [],  # Quick replies dihapus
            "event_cards": [],
            "intent": "welcome",
        }

    def ensure_welcome_message() -> None:
        """Pastikan pesan selamat datang ada di awal history."""
        history = SessionManager.get_chat_history()
        if not history:
            welcome = get_welcome_message()
            SessionManager.add_chat_message(
                role=welcome["role"],
                content=welcome["content"],
                extra={
                    "quick_replies": welcome["quick_replies"],
                    "event_cards": welcome["event_cards"],
                    "intent": welcome["intent"],
                },
            )

    return {
        "messages": SessionManager.get_chat_history(),
        "is_typing": is_typing(),
        "send_message": send_message,
        "clear_history": clear_history,
        "load_history_from_backend": load_history_from_backend,
        "get_suggested_questions": get_suggested_questions,
        "get_typing_placeholder": get_typing_placeholder,
        "get_welcome_message": get_welcome_message,
        "ensure_welcome_message": ensure_welcome_message,
        "session_token": SessionManager.get_chat_session(),
    }
