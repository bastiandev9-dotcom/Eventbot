"""
Ticket Model
============
CRUD operations untuk tabel tickets.
"""

from backend.config import execute_query
from typing import Optional, List, Dict, Any


class TicketModel:
    """Model untuk tabel tickets."""

    TABLE = "tickets"

    @classmethod
    def create(cls, event_id: str, name: str, price: float,
               quantity: int, description: str = None,
               max_per_order: int = 5, benefits: list = None,
               sale_starts_at: str = None, sale_ends_at: str = None) -> Optional[Dict]:
        """Buat tiket baru untuk event."""
        sql = """
            INSERT INTO tickets (event_id, name, description, price, quantity,
                               max_per_order, benefits, sale_starts_at, sale_ends_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, event_id, name, price, quantity, status, created_at;
        """
        params = (event_id, name, description, price, quantity, 
                  max_per_order, benefits, sale_starts_at, sale_ends_at)
        return execute_query(sql, params, fetch_one=True)

    @classmethod
    def get_by_id(cls, ticket_id: str) -> Optional[Dict]:
        """Ambil tiket berdasarkan ID."""
        sql = """
            SELECT t.*, e.title as event_title, e.start_date, e.location
            FROM tickets t
            JOIN events e ON t.event_id = e.id
            WHERE t.id = %s AND t.deleted_at IS NULL;
        """
        return execute_query(sql, (ticket_id,), fetch_one=True)

    @classmethod
    def get_by_event(cls, event_id: str) -> List[Dict]:
        """Ambil semua tiket untuk sebuah event."""
        sql = """
            SELECT t.*, (t.quantity - t.sold) as remaining
            FROM tickets t
            WHERE t.event_id = %s AND t.deleted_at IS NULL
            ORDER BY t.price ASC;
        """
        return execute_query(sql, (event_id,), fetch_all=True) or []

    @classmethod
    def check_availability(cls, ticket_id: str) -> Optional[Dict]:
        """Cek ketersediaan tiket via stored function."""
        return execute_query(
            "SELECT * FROM check_ticket_availability(%s)",
            (ticket_id,), fetch_one=True
        )

    @classmethod
    def update(cls, ticket_id: str, **kwargs) -> Optional[Dict]:
        """Update tiket."""
        allowed = ['name', 'description', 'price', 'quantity', 'max_per_order',
                   'benefits', 'status', 'sale_starts_at', 'sale_ends_at']
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [ticket_id]

        sql = f"""
            UPDATE tickets SET {set_clause}
            WHERE id = %s AND deleted_at IS NULL
            RETURNING id, name, price, quantity, sold, status;
        """
        return execute_query(sql, tuple(values), fetch_one=True)

    @classmethod
    def delete(cls, ticket_id: str) -> bool:
        """Soft delete tiket."""
        result = execute_query(
            "UPDATE tickets SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s",
            (ticket_id,)
        )
        return result > 0

    @classmethod
    def get_stats_by_event(cls, event_id: str) -> Optional[Dict]:
        """Get statistik tiket per event."""
        sql = """
            SELECT 
                COUNT(*) as total_types,
                COALESCE(SUM(quantity), 0) as total_capacity,
                COALESCE(SUM(sold), 0) as total_sold,
                COALESCE(SUM(quantity - sold), 0) as total_remaining,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM tickets
            WHERE event_id = %s AND deleted_at IS NULL;
        """
        return execute_query(sql, (event_id,), fetch_one=True)