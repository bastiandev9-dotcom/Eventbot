"""
Base Repository
===============
Generic CRUD base class yang bisa di-extend.
"""

from backend.config import execute_query
from typing import Optional, List, Dict, Any


class BaseRepository:
    """Base repository dengan generic CRUD operations."""

    TABLE = None  # Override di subclass

    @classmethod
    def get_by_id(cls, record_id: str) -> Optional[Dict]:
        """Ambil by ID."""
        sql = f"SELECT * FROM {cls.TABLE} WHERE id = %s AND deleted_at IS NULL;"
        return execute_query(sql, (record_id,), fetch_one=True)

    @classmethod
    def list_all(cls, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List semua record."""
        sql = f"""
            SELECT * FROM {cls.TABLE}
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s;
        """
        return execute_query(sql, (limit, offset), fetch_all=True) or []

    @classmethod
    def soft_delete(cls, record_id: str) -> bool:
        """Soft delete."""
        sql = f"UPDATE {cls.TABLE} SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s;"
        result = execute_query(sql, (record_id,))
        return result > 0

    @classmethod
    def hard_delete(cls, record_id: str) -> bool:
        """Hard delete (hati-hati!)."""
        sql = f"DELETE FROM {cls.TABLE} WHERE id = %s;"
        result = execute_query(sql, (record_id,))
        return result > 0

    @classmethod
    def count(cls) -> int:
        """Hitung total record."""
        sql = f"SELECT COUNT(*) as count FROM {cls.TABLE} WHERE deleted_at IS NULL;"
        result = execute_query(sql, fetch_one=True)
        return result['count'] if result else 0