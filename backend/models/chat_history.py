"""
Chat Models
===========
CRUD operations untuk chat_sessions dan chat_messages.
"""

from backend.config import execute_query
from typing import Optional, List, Dict


class ChatSessionModel:
    """Model untuk tabel chat_sessions."""

    TABLE = "chat_sessions"

    @classmethod
    def create(cls, user_id: str = None, ip_address: str = None, 
                 user_agent: str = None) -> Optional[Dict]:
        """Buat sesi chat baru via stored function, dengan fallback INSERT langsung."""
        try:
            result = execute_query(
                "SELECT * FROM create_chat_session(%s, %s::inet, %s)",
                (user_id, ip_address, user_agent),
                fetch_one=True
            )
            # Pastikan result punya key session_token
            if result and 'session_token' in result:
                return result
        except Exception:
            pass

        # Fallback: INSERT langsung ke tabel
        from backend.config import generate_session_token
        token = generate_session_token()
        sql = """
            INSERT INTO chat_sessions (user_id, session_token)
            VALUES (%s, %s)
            RETURNING id, session_token, started_at;
        """
        return execute_query(sql, (user_id, token), fetch_one=True)

    @classmethod
    def get_by_id(cls, session_id: str) -> Optional[Dict]:
        """Ambil sesi chat."""
        sql = """
            SELECT * FROM chat_sessions
            WHERE id = %s;
        """
        return execute_query(sql, (session_id,), fetch_one=True)

    @classmethod
    def get_by_token(cls, session_token: str) -> Optional[Dict]:
        """Ambil sesi by token."""
        sql = "SELECT * FROM chat_sessions WHERE session_token = %s;"
        return execute_query(sql, (session_token,), fetch_one=True)

    @classmethod
    def end_session(cls, session_id: str) -> bool:
        """Akhiri sesi chat."""
        result = execute_query(
            "UPDATE chat_sessions SET ended_at = CURRENT_TIMESTAMP WHERE id = %s",
            (session_id,)
        )
        return result > 0

    @classmethod
    def get_user_sessions(cls, user_id: str, limit: int = 10) -> List[Dict]:
        """Ambil history sesi user."""
        sql = """
            SELECT id, session_token, started_at, last_activity_at, ended_at
            FROM chat_sessions
            WHERE user_id = %s
            ORDER BY started_at DESC
            LIMIT %s;
        """
        return execute_query(sql, (user_id, limit), fetch_all=True) or []


class ChatMessageModel:
    """Model untuk tabel chat_messages."""

    TABLE = "chat_messages"

    @classmethod
    def create(cls, session_id: str, role: str, content: str,
               intent: str = None, entities: dict = None) -> Optional[Dict]:
        """Simpan pesan chat, dengan fallback INSERT langsung jika stored function gagal."""
        import json as _json
        # Serialise entities ke JSON string agar psycopg2 bisa adapt
        entities_json = _json.dumps(entities, ensure_ascii=False) if entities else None

        try:
            return execute_query(
                "SELECT * FROM save_chat_message(%s, %s, %s, %s, %s)",
                (session_id, role, content, intent, entities_json),
                fetch_one=True
            )
        except Exception:
            pass

        # Fallback: INSERT langsung
        sql = """
            INSERT INTO chat_messages (session_id, role, content, intent, entities)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            RETURNING id, session_id, role, content, created_at;
        """
        return execute_query(
            sql,
            (session_id, role, content, intent, entities_json),
            fetch_one=True
        )

    @classmethod
    def get_history(cls, session_id: str, limit: int = 50) -> List[Dict]:
        """Ambil history chat."""
        return execute_query(
            "SELECT * FROM get_chat_history(%s, %s)",
            (session_id, limit),
            fetch_all=True
        ) or []

    @classmethod
    def get_recent_messages(cls, session_id: str, limit: int = 10) -> List[Dict]:
        """Ambil pesan terakhir (untuk context)."""
        sql = """
            SELECT role, content, intent, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
        """
        return execute_query(sql, (session_id, limit), fetch_all=True) or []