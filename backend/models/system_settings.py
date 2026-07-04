"""
System Settings Model
=====================
CRUD operations untuk tabel system_settings.
"""

from backend.config import execute_query
from typing import Optional, List, Dict


class SystemSettingsModel:
    """Model untuk tabel system_settings."""

    TABLE = "system_settings"

    @classmethod
    def get(cls, key: str) -> Optional[str]:
        """Ambil value by key."""
        sql = "SELECT value FROM system_settings WHERE key = %s;"
        result = execute_query(sql, (key,), fetch_one=True)
        return result['value'] if result else None

    @classmethod
    def get_all(cls) -> List[Dict]:
        """Ambil semua settings."""
        sql = "SELECT key, value, description, updated_at FROM system_settings;"
        return execute_query(sql, fetch_all=True) or []

    @classmethod
    def set(cls, key: str, value: str, description: str = None) -> bool:
        """Set/update value."""
        sql = """
            INSERT INTO system_settings (key, value, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                description = COALESCE(EXCLUDED.description, system_settings.description),
                updated_at = CURRENT_TIMESTAMP;
        """
        result = execute_query(sql, (key, value, description))
        return result > 0

    @classmethod
    def delete(cls, key: str) -> bool:
        """Hapus setting."""
        result = execute_query(
            "DELETE FROM system_settings WHERE key = %s",
            (key,)
        )
        return result > 0

    @classmethod
    def get_chatbot_settings(cls) -> Dict:
        """Ambil semua chatbot settings."""
        keys = ['chatbot_name', 'chatbot_greeting', 'chatbot_fallback', 'max_chat_history']
        sql = """
            SELECT key, value FROM system_settings
            WHERE key = ANY(%s);
        """
        results = execute_query(sql, (keys,), fetch_all=True) or []
        return {row['key']: row['value'] for row in results}