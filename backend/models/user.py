"""
User Model
==========
CRUD operations untuk tabel users.
"""

from backend.config import execute_query, get_db_cursor
from backend.config.security import hash_password, verify_password
from typing import Optional, List, Dict, Any


class UserModel:
    """Model untuk tabel users."""

    TABLE = "users"

    @classmethod
    def create(cls, name: str, email: str, password: str, 
               role: str = 'participant', phone: str = None, 
               avatar_url: str = None) -> Optional[Dict]:
        """Buat user baru. Return user dict atau None."""
        password_hash = hash_password(password)

        sql = """
            INSERT INTO users (name, email, password_hash, role, phone, avatar_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, email, role, status, created_at;
        """
        return execute_query(sql, (name, email, password_hash, role, phone, avatar_url), 
                            fetch_one=True)

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[Dict]:
        """Ambil user berdasarkan ID."""
        sql = """
            SELECT id, name, email, phone, avatar_url, role, status,
                   email_verified_at, last_login_at, created_at
            FROM users
            WHERE id = %s AND deleted_at IS NULL;
        """
        return execute_query(sql, (user_id,), fetch_one=True)

    @classmethod
    def get_by_email(cls, email: str) -> Optional[Dict]:
        """Ambil user berdasarkan email (untuk login)."""
        sql = """
            SELECT id, name, email, password_hash, role, status, 
                   email_verified_at, last_login_at
            FROM users
            WHERE email = %s AND deleted_at IS NULL;
        """
        return execute_query(sql, (email,), fetch_one=True)

    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional[Dict]:
        """Autentikasi user. Return user data jika valid, None jika tidak."""
        user = cls.get_by_email(email)
        if user and verify_password(password, user['password_hash']):
            # Update last_login
            execute_query(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            return user
        return None

    @classmethod
    def update(cls, user_id: str, **kwargs) -> Optional[Dict]:
        """Update user fields. kwargs = field:value yang mau diupdate."""
        allowed_fields = ['name', 'email', 'phone', 'avatar_url', 'role', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [user_id]

        sql = f"""
            UPDATE users SET {set_clause}
            WHERE id = %s AND deleted_at IS NULL
            RETURNING id, name, email, role, status, updated_at;
        """
        return execute_query(sql, tuple(values), fetch_one=True)

    @classmethod
    def update_password(cls, user_id: str, new_password: str) -> bool:
        """Update password user."""
        password_hash = hash_password(new_password)
        result = execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s AND deleted_at IS NULL",
            (password_hash, user_id)
        )
        return result > 0

    @classmethod
    def delete(cls, user_id: str) -> bool:
        """Soft delete user."""
        result = execute_query(
            "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
            (user_id,)
        )
        return result > 0

    @classmethod
    def list_all(cls, role: str = None, status: str = None, 
                 limit: int = 20, offset: int = 0) -> List[Dict]:
        """List users dengan filter."""
        conditions = ["deleted_at IS NULL"]
        params = []

        if role:
            conditions.append("role = %s")
            params.append(role)
        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions)
        params.extend([limit, offset])

        sql = f"""
            SELECT id, name, email, phone, role, status, created_at
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s;
        """
        return execute_query(sql, tuple(params), fetch_all=True) or []

    @classmethod
    def count(cls, role: str = None, status: str = None) -> int:
        """Hitung jumlah user."""
        conditions = ["deleted_at IS NULL"]
        params = []

        if role:
            conditions.append("role = %s")
            params.append(role)
        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions)

        sql = f"SELECT COUNT(*) as count FROM users WHERE {where_clause};"
        result = execute_query(sql, tuple(params), fetch_one=True)
        return result['count'] if result else 0