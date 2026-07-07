"""
Session Manager
===============
Mengelola Streamlit session state untuk autentikasi dan data user.
"""

import streamlit as st
from typing import Optional, Dict, Any


class SessionManager:
    """Wrapper untuk st.session_state yang type-safe dan terstruktur."""

    # ── Keys ──────────────────────────────────────────────
    KEY_USER = "user"
    KEY_TOKEN = "access_token"
    KEY_ROLE = "user_role"
    KEY_LOGGED_IN = "is_logged_in"
    KEY_CHAT_SESSION = "chat_session_token"
    KEY_CHAT_HISTORY = "chat_history"
    KEY_CURRENT_PAGE = "current_page"
    KEY_THEME = "theme"
    KEY_NOTIFICATIONS = "notifications"
    KEY_TOAST = "toast_message"

    @classmethod
    def init(cls) -> None:
        """Inisialisasi semua key session state dengan default value."""
        defaults: Dict[str, Any] = {
            cls.KEY_USER: None,
            cls.KEY_TOKEN: None,
            cls.KEY_ROLE: "guest",
            cls.KEY_LOGGED_IN: False,
            cls.KEY_CHAT_SESSION: None,
            cls.KEY_CHAT_HISTORY: [],
            cls.KEY_CURRENT_PAGE: "Landing",
            cls.KEY_THEME: "dark",
            cls.KEY_NOTIFICATIONS: [],
            cls.KEY_TOAST: None,
        }
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default

    # ── Auth ──────────────────────────────────────────────

    @classmethod
    def login(cls, user: Dict[str, Any], token: str) -> None:
        """Simpan data user setelah login berhasil."""
        st.session_state[cls.KEY_USER] = user
        st.session_state[cls.KEY_TOKEN] = token
        st.session_state[cls.KEY_ROLE] = user.get("role", "participant")
        st.session_state[cls.KEY_LOGGED_IN] = True

    @classmethod
    def logout(cls) -> None:
        """Hapus semua data sesi user."""
        st.session_state[cls.KEY_USER] = None
        st.session_state[cls.KEY_TOKEN] = None
        st.session_state[cls.KEY_ROLE] = "guest"
        st.session_state[cls.KEY_LOGGED_IN] = False
        st.session_state[cls.KEY_CHAT_SESSION] = None
        st.session_state[cls.KEY_CHAT_HISTORY] = []

    @classmethod
    def is_logged_in(cls) -> bool:
        return bool(st.session_state.get(cls.KEY_LOGGED_IN, False))

    @classmethod
    def get_token(cls) -> Optional[str]:
        return st.session_state.get(cls.KEY_TOKEN)

    @classmethod
    def get_user(cls) -> Optional[Dict[str, Any]]:
        return st.session_state.get(cls.KEY_USER)

    @classmethod
    def get_role(cls) -> str:
        return st.session_state.get(cls.KEY_ROLE, "guest")

    @classmethod
    def is_admin(cls) -> bool:
        return cls.get_role() == "admin"

    @classmethod
    def is_participant(cls) -> bool:
        return cls.get_role() == "participant"

    # ── Chat ──────────────────────────────────────────────

    @classmethod
    def get_chat_session(cls) -> Optional[str]:
        return st.session_state.get(cls.KEY_CHAT_SESSION)

    @classmethod
    def set_chat_session(cls, token: str) -> None:
        st.session_state[cls.KEY_CHAT_SESSION] = token

    @classmethod
    def get_chat_history(cls) -> list:
        return st.session_state.get(cls.KEY_CHAT_HISTORY, [])

    @classmethod
    def add_chat_message(cls, role: str, content: str, extra: Optional[Dict] = None) -> None:
        """Tambah pesan ke history chat lokal.

        Args:
            role: 'user' atau 'bot'
            content: Teks pesan
            extra: Data tambahan (quick_replies, event_cards, dll)
        """
        history = cls.get_chat_history()
        message = {"role": role, "content": content}
        if extra:
            message.update(extra)
        history.append(message)
        st.session_state[cls.KEY_CHAT_HISTORY] = history

    @classmethod
    def clear_chat_history(cls) -> None:
        st.session_state[cls.KEY_CHAT_HISTORY] = []
        st.session_state[cls.KEY_CHAT_SESSION] = None

    # ── Theme ─────────────────────────────────────────────

    @classmethod
    def get_theme(cls) -> str:
        return "dark"

    @classmethod
    def set_theme(cls, theme: str) -> None:
        # Tema selalu dark — metode ini dipertahankan untuk kompatibilitas
        pass

    # ── Notifications ─────────────────────────────────────

    @classmethod
    def get_notifications(cls) -> list:
        return st.session_state.get(cls.KEY_NOTIFICATIONS, [])

    @classmethod
    def add_notification(cls, message: str, notif_type: str = "info") -> None:
        notifs = cls.get_notifications()
        notifs.append({"message": message, "type": notif_type, "read": False})
        st.session_state[cls.KEY_NOTIFICATIONS] = notifs

    @classmethod
    def get_unread_count(cls) -> int:
        return sum(1 for n in cls.get_notifications() if not n.get("read"))

    @classmethod
    def mark_all_read(cls) -> None:
        notifs = cls.get_notifications()
        for n in notifs:
            n["read"] = True
        st.session_state[cls.KEY_NOTIFICATIONS] = notifs

    # ── Toast ─────────────────────────────────────────────

    @classmethod
    def show_toast(cls, message: str, toast_type: str = "success") -> None:
        """Set toast message yang akan ditampilkan di render berikutnya."""
        st.session_state[cls.KEY_TOAST] = {"message": message, "type": toast_type}

    @classmethod
    def pop_toast(cls) -> Optional[Dict[str, str]]:
        """Ambil dan hapus toast message (dipanggil sekali saat render)."""
        toast = st.session_state.get(cls.KEY_TOAST)
        st.session_state[cls.KEY_TOAST] = None
        return toast

    # ── Generic get/set ───────────────────────────────────

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        st.session_state[key] = value
