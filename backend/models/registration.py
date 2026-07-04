"""
Registration Model
==================
CRUD operations untuk tabel registrations (booking).
"""

from backend.config import execute_query
from typing import Optional, List, Dict, Any


class RegistrationModel:
    """Model untuk tabel registrations."""

    TABLE = "registrations"

    @classmethod
    def create(cls, user_id: str, ticket_id: str, quantity: int = 1,
               payment_method: str = None) -> Optional[Dict]:
        """Buat registrasi via stored function (dengan validasi)."""
        result = execute_query(
            "SELECT * FROM register_to_event(%s, %s, %s, %s)",
            (user_id, ticket_id, quantity, payment_method),
            fetch_one=True
        )
        return result

    @classmethod
    def get_by_id(cls, registration_id: str) -> Optional[Dict]:
        """Ambil detail registrasi."""
        sql = """
            SELECT r.*, 
                   e.title as event_title, e.start_date, e.location,
                   t.name as ticket_name, t.price as ticket_price,
                   u.name as user_name, u.email as user_email
            FROM registrations r
            JOIN events e ON r.event_id = e.id
            JOIN tickets t ON r.ticket_id = t.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s;
        """
        return execute_query(sql, (registration_id,), fetch_one=True)

    @classmethod
    def get_by_user(cls, user_id: str, status: str = None) -> List[Dict]:
        """Ambil semua registrasi user."""
        conditions = ["r.user_id = %s", "r.cancelled_at IS NULL"]
        params = [user_id]

        if status:
            conditions.append("r.status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT r.id, r.quantity, r.total_price, r.status, r.created_at,
                   e.id as event_id, e.title as event_title, e.start_date, 
                   e.location, e.image_url,
                   t.name as ticket_name
            FROM registrations r
            JOIN events e ON r.event_id = e.id
            JOIN tickets t ON r.ticket_id = t.id
            WHERE {where_clause}
            ORDER BY r.created_at DESC;
        """
        return execute_query(sql, tuple(params), fetch_all=True) or []

    @classmethod
    def update_status(cls, registration_id: str, status: str) -> Optional[Dict]:
        """Update status registrasi (pending -> confirmed -> attended)."""
        sql = """
            UPDATE registrations SET status = %s
            WHERE id = %s
            RETURNING id, status, updated_at;
        """
        return execute_query(sql, (status, registration_id), fetch_one=True)

    @classmethod
    def cancel(cls, registration_id: str) -> bool:
        """Cancel registrasi."""
        result = execute_query(
            "UPDATE registrations SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP WHERE id = %s",
            (registration_id,)
        )
        return result > 0

    @classmethod
    def check_in(cls, registration_id: str, checked_in_by: str) -> Optional[Dict]:
        """Check-in peserta di venue."""
        sql = """
            UPDATE registrations 
            SET checked_in_at = CURRENT_TIMESTAMP, checked_in_by = %s, status = 'attended'
            WHERE id = %s AND status = 'confirmed'
            RETURNING id, checked_in_at, status;
        """
        return execute_query(sql, (checked_in_by, registration_id), fetch_one=True)

    @classmethod
    def get_event_registrations(cls, event_id: str) -> List[Dict]:
        """Ambil semua registrasi untuk sebuah event."""
        sql = """
            SELECT r.id, r.quantity, r.total_price, r.status, r.created_at,
                   u.name as user_name, u.email, t.name as ticket_name
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            JOIN tickets t ON r.ticket_id = t.id
            WHERE r.event_id = %s AND r.cancelled_at IS NULL
            ORDER BY r.created_at DESC;
        """
        return execute_query(sql, (event_id,), fetch_all=True) or []