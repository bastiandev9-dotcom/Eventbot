"""
Category Model
==============
CRUD operations untuk tabel categories.
"""

from backend.config import execute_query
from typing import Optional, List, Dict


class CategoryModel:
    """Model untuk tabel categories."""

    TABLE = "categories"

    @classmethod
    def create(cls, name: str, slug: str, description: str = None,
               color: str = '#3B82F6', icon: str = None) -> Optional[Dict]:
        """Buat kategori baru."""
        sql = """
            INSERT INTO categories (name, slug, description, color, icon)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, slug, color, icon, created_at;
        """
        return execute_query(sql, (name, slug, description, color, icon), fetch_one=True)

    @classmethod
    def get_by_id(cls, category_id: str) -> Optional[Dict]:
        """Ambil kategori by ID."""
        sql = "SELECT * FROM categories WHERE id = %s;"
        return execute_query(sql, (category_id,), fetch_one=True)

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional[Dict]:
        """Ambil kategori by slug."""
        sql = "SELECT * FROM categories WHERE slug = %s;"
        return execute_query(sql, (slug,), fetch_one=True)

    @classmethod
    def list_all(cls) -> List[Dict]:
        """List semua kategori."""
        sql = """
            SELECT c.*, COUNT(ec.event_id) as event_count
            FROM categories c
            LEFT JOIN event_categories ec ON c.id = ec.category_id
            GROUP BY c.id
            ORDER BY c.name;
        """
        return execute_query(sql, fetch_all=True) or []

    @classmethod
    def update(cls, category_id: str, **kwargs) -> Optional[Dict]:
        """Update kategori."""
        allowed = ['name', 'slug', 'description', 'color', 'icon']
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [category_id]

        sql = f"""
            UPDATE categories SET {set_clause}
            WHERE id = %s
            RETURNING id, name, slug, color, updated_at;
        """
        return execute_query(sql, tuple(values), fetch_one=True)

    @classmethod
    def delete(cls, category_id: str) -> bool:
        """Hapus kategori."""
        result = execute_query(
            "DELETE FROM categories WHERE id = %s",
            (category_id,)
        )
        return result > 0