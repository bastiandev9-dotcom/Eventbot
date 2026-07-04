"""
Knowledge Base Model
====================
CRUD operations untuk tabel knowledge_base (FAQ chatbot).
"""

from backend.config import execute_query
from typing import Optional, List, Dict


class KnowledgeBaseModel:
    """Model untuk tabel knowledge_base."""

    TABLE = "knowledge_base"

    @classmethod
    def create(cls, category: str, question: str, answer: str,
               keywords: list = None, priority: int = 0) -> Optional[Dict]:
        """Tambah FAQ baru."""
        sql = """
            INSERT INTO knowledge_base (category, question, answer, keywords, priority)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, category, question, priority, is_active, created_at;
        """
        return execute_query(sql, (category, question, answer, keywords, priority), fetch_one=True)

    @classmethod
    def search(cls, query: str, limit: int = 3) -> List[Dict]:
        """Cari FAQ menggunakan ILIKE (tanpa pg_trgm)."""
        sql = """
            SELECT id, category, question, answer, keywords, priority
            FROM knowledge_base
            WHERE is_active = TRUE
              AND (
                  question ILIKE %s
                  OR answer ILIKE %s
                  OR %s = ANY(keywords)
              )
            ORDER BY
                CASE WHEN question ILIKE %s THEN 0 ELSE 1 END,
                priority DESC
            LIMIT %s;
        """
        like_q = f"%{query}%"
        return execute_query(
            sql,
            (like_q, like_q, query, like_q, limit),
            fetch_all=True
        ) or []

    @classmethod
    def get_by_category(cls, category: str) -> List[Dict]:
        """Ambil FAQ by kategori."""
        sql = """
            SELECT id, question, answer, keywords, priority
            FROM knowledge_base
            WHERE category = %s AND is_active = TRUE
            ORDER BY priority DESC;
        """
        return execute_query(sql, (category,), fetch_all=True) or []

    @classmethod
    def update(cls, kb_id: str, **kwargs) -> Optional[Dict]:
        """Update FAQ."""
        allowed = ['category', 'question', 'answer', 'keywords', 'priority', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [kb_id]

        sql = f"""
            UPDATE knowledge_base SET {set_clause}
            WHERE id = %s
            RETURNING id, question, updated_at;
        """
        return execute_query(sql, tuple(values), fetch_one=True)

    @classmethod
    def delete(cls, kb_id: str) -> bool:
        """Hapus FAQ (hard delete)."""
        result = execute_query(
            "DELETE FROM knowledge_base WHERE id = %s",
            (kb_id,)
        )
        return result > 0

    @classmethod
    def list_all(cls, category: str = None, active_only: bool = True) -> List[Dict]:
        """List semua FAQ."""
        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)
        if active_only:
            conditions.append("is_active = TRUE")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
            SELECT id, category, question, answer, keywords, priority, is_active
            FROM knowledge_base
            WHERE {where_clause}
            ORDER BY category, priority DESC;
        """
        return execute_query(sql, tuple(params), fetch_all=True) or []