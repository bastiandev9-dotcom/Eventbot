"""
Event Model
===========
CRUD operations untuk tabel events.
"""

from backend.config import execute_query
from typing import Optional, List, Dict, Any


class EventModel:
    """Model untuk tabel events."""

    TABLE = "events"

    @classmethod
    def create(cls, title: str, description: str, short_description: str,
               start_date: str, end_date: str, location: str,
               organizer_id: str, **kwargs) -> Optional[Dict]:
        """Buat event baru. Slug auto-generate via trigger."""
        sql = """
            INSERT INTO events (
                title, description, short_description, start_date, end_date,
                start_time, end_time, location, location_map_url, organizer_id,
                image_url, banner_url, capacity, status, is_published
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, slug, start_date, end_date, location, status, created_at;
        """
        params = (
            title, description, short_description,
            start_date, end_date,
            kwargs.get('start_time'), kwargs.get('end_time'),
            location, kwargs.get('location_map_url'),
            organizer_id,
            kwargs.get('image_url'), kwargs.get('banner_url'),
            kwargs.get('capacity', 0), kwargs.get('status', 'upcoming'),
            kwargs.get('is_published', False)
        )
        return execute_query(sql, params, fetch_one=True)

    @classmethod
    def get_by_id(cls, event_id: str) -> Optional[Dict]:
        """Ambil event detail lengkap beserta daftar tiketnya."""
        # Query event utama
        sql = """
            SELECT
                e.id, e.title, e.slug, e.description, e.short_description,
                e.start_date, e.end_date, e.start_time, e.end_time,
                e.location, e.location_map_url, e.image_url, e.banner_url,
                e.capacity, e.status, e.view_count, e.is_published,
                u.name AS organizer_name, u.id AS organizer_id,
                COALESCE(reg.registered_count, 0) AS registered_count
            FROM events e
            JOIN users u ON e.organizer_id = u.id
            LEFT JOIN (
                SELECT event_id, COUNT(*) AS registered_count
                FROM registrations
                WHERE status = 'confirmed'
                GROUP BY event_id
            ) reg ON reg.event_id = e.id
            WHERE e.id = %s AND e.deleted_at IS NULL;
        """
        event = execute_query(sql, (event_id,), fetch_one=True)
        if not event:
            return None

        # Query tiket untuk event ini
        ticket_sql = """
            SELECT
                t.id, t.name, t.description, t.price,
                t.quantity AS quota, t.sold AS sold_count,
                t.max_per_order, t.status,
                t.sale_starts_at, t.sale_ends_at,
                (t.quantity - t.sold) AS remaining
            FROM tickets t
            WHERE t.event_id = %s AND t.deleted_at IS NULL
            ORDER BY t.price ASC;
        """
        tickets = execute_query(ticket_sql, (event_id,), fetch_all=True) or []
        event["tickets"] = tickets
        return event

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional[Dict]:
        """Ambil event berdasarkan slug."""
        sql = """
            SELECT e.*, u.name as organizer_name
            FROM events e
            JOIN users u ON e.organizer_id = u.id
            WHERE e.slug = %s AND e.deleted_at IS NULL;
        """
        return execute_query(sql, (slug,), fetch_one=True)

    @classmethod
    def search(cls, query: str = None, location: str = None,
               category_slug: str = None, start_date: str = None,
               end_date: str = None, status: str = None,
               min_price: float = None, max_price: float = None,
               is_published: bool = True,   # False = tampilkan semua (untuk admin)
               limit: int = 20, offset: int = 0) -> List[Dict]:
        """Cari event dengan filter dinamis. status=None menampilkan semua status."""
        conditions = ["e.deleted_at IS NULL"]
        if is_published:
            conditions.append("e.is_published = TRUE")
        params: List[Any] = []

        if status:   # hanya filter jika status diisi
            conditions.append("e.status = %s::event_status")
            params.append(status)
        if location:
            conditions.append("e.location ILIKE %s")
            params.append(f"%{location}%")
        if category_slug:
            conditions.append("c.slug = %s")
            params.append(category_slug)
        if start_date:
            conditions.append("e.start_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("e.end_date <= %s")
            params.append(end_date)
        if query:
            conditions.append(
                "(e.title ILIKE %s OR e.description ILIKE %s OR e.location ILIKE %s)"
            )
            like_q = f"%{query}%"
            params.extend([like_q, like_q, like_q])

        where_clause = " AND ".join(conditions)

        having_clauses = []
        if min_price is not None:
            having_clauses.append("MIN(t.price) >= %s")
            params.append(min_price)
        if max_price is not None:
            having_clauses.append("MIN(t.price) <= %s")
            params.append(max_price)

        having_sql = f"HAVING {' AND '.join(having_clauses)}" if having_clauses else ""

        params.extend([limit, offset])

        sql = f"""
            SELECT
                e.id, e.title, e.slug, e.short_description,
                e.start_date, e.end_date, e.location, e.image_url,
                e.status, e.capacity, e.view_count, e.is_published,
                u.name AS organizer_name,
                MIN(t.price) AS min_price,
                COALESCE(SUM(t.quantity), 0)::int AS total_quota,
                COALESCE(SUM(t.sold), 0)::int     AS total_sold,
                COALESCE(MAX(reg.registered_count), 0) AS registered_count
            FROM events e
            JOIN users u ON e.organizer_id = u.id
            LEFT JOIN event_categories ec ON e.id = ec.event_id
            LEFT JOIN categories c ON ec.category_id = c.id
            LEFT JOIN tickets t ON e.id = t.event_id AND t.deleted_at IS NULL
            LEFT JOIN (
                SELECT event_id, COUNT(*) AS registered_count
                FROM registrations
                WHERE status = 'confirmed'
                GROUP BY event_id
            ) reg ON reg.event_id = e.id
            WHERE {where_clause}
            GROUP BY e.id, e.title, e.slug, e.short_description,
                     e.start_date, e.end_date, e.location, e.image_url,
                     e.status, e.capacity, e.view_count, e.is_published, u.name
            {having_sql}
            ORDER BY e.start_date ASC, e.id ASC
            LIMIT %s OFFSET %s;
        """
        return execute_query(sql, tuple(params), fetch_all=True) or []

    @classmethod
    def count_search(cls, query: str = None, location: str = None,
                     category_slug: str = None, start_date: str = None,
                     end_date: str = None, status: str = None,
                     min_price: float = None, max_price: float = None,
                     is_published: bool = True) -> int:
        """Hitung total event yang cocok dengan filter (tanpa LIMIT/OFFSET)."""
        conditions = ["e.deleted_at IS NULL"]
        if is_published:
            conditions.append("e.is_published = TRUE")
        params: List[Any] = []

        if status:
            conditions.append("e.status = %s::event_status")
            params.append(status)
        if location:
            conditions.append("e.location ILIKE %s")
            params.append(f"%{location}%")
        if category_slug:
            conditions.append("c.slug = %s")
            params.append(category_slug)
        if start_date:
            conditions.append("e.start_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("e.end_date <= %s")
            params.append(end_date)
        if query:
            conditions.append(
                "(e.title ILIKE %s OR e.description ILIKE %s OR e.location ILIKE %s)"
            )
            like_q = f"%{query}%"
            params.extend([like_q, like_q, like_q])

        having_clauses = []
        if min_price is not None:
            having_clauses.append("MIN(t.price) >= %s")
            params.append(min_price)
        if max_price is not None:
            having_clauses.append("MIN(t.price) <= %s")
            params.append(max_price)

        where_clause = " AND ".join(conditions)
        having_sql   = f"HAVING {' AND '.join(having_clauses)}" if having_clauses else ""

        sql = f"""
            SELECT COUNT(*) AS total FROM (
                SELECT e.id
                FROM events e
                JOIN users u ON e.organizer_id = u.id
                LEFT JOIN event_categories ec ON e.id = ec.event_id
                LEFT JOIN categories c ON ec.category_id = c.id
                LEFT JOIN tickets t ON e.id = t.event_id AND t.deleted_at IS NULL
                WHERE {where_clause}
                GROUP BY e.id
                {having_sql}
            ) sub;
        """
        result = execute_query(sql, tuple(params), fetch_one=True)
        return int(result["total"]) if result else 0

    @classmethod
    def update(cls, event_id: str, **kwargs) -> Optional[Dict]:
        """Update event fields."""
        allowed = ['title', 'description', 'short_description', 'start_date', 
                   'end_date', 'start_time', 'end_time', 'location', 
                   'location_map_url', 'image_url', 'banner_url', 'capacity',
                   'status', 'is_published']
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return None

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [event_id]

        sql = f"""
            UPDATE events SET {set_clause}
            WHERE id = %s AND deleted_at IS NULL
            RETURNING id, title, slug, status, updated_at;
        """
        return execute_query(sql, tuple(values), fetch_one=True)

    @classmethod
    def delete(cls, event_id: str) -> bool:
        """Soft delete event secara atomic (cascade ke tiket dalam satu transaksi)."""
        from backend.config import get_db_connection
        from psycopg2.extras import RealDictCursor

        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Soft-delete event
                    cur.execute(
                        "UPDATE events SET deleted_at = CURRENT_TIMESTAMP "
                        "WHERE id = %s AND deleted_at IS NULL",
                        (event_id,)
                    )
                    affected = cur.rowcount

                    if affected == 0:
                        # Event tidak ditemukan atau sudah dihapus — bukan error
                        conn.rollback()
                        return False

                    # Soft-delete semua tiket terkait (boleh 0 tiket)
                    cur.execute(
                        "UPDATE tickets SET deleted_at = CURRENT_TIMESTAMP "
                        "WHERE event_id = %s AND deleted_at IS NULL",
                        (event_id,)
                    )

                    conn.commit()
                    return True
        except Exception as e:
            # Log error tapi jangan crash — kembalikan False agar service menangani dengan baik
            import traceback
            print(f"[EventModel.delete] Error saat menghapus event {event_id}: {e}")
            traceback.print_exc()
            return False

    @classmethod
    def list_by_organizer(cls, organizer_id: str, 
                          limit: int = 20, offset: int = 0) -> List[Dict]:
        """List event milik organizer."""
        sql = """
            SELECT id, title, slug, start_date, end_date, location, 
                   status, is_published, view_count, created_at
            FROM events
            WHERE organizer_id = %s AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s;
        """
        return execute_query(sql, (organizer_id, limit, offset), fetch_all=True) or []

    @classmethod
    def get_recommended(cls, event_id: str, limit: int = 3) -> List[Dict]:
        """Get rekomendasi event serupa."""
        return execute_query(
            "SELECT * FROM get_recommended_events(%s, %s)",
            (event_id, limit), fetch_all=True
        ) or []

    @classmethod
    def increment_view(cls, event_id: str) -> bool:
        """Increment view count."""
        result = execute_query(
            "UPDATE events SET view_count = view_count + 1 WHERE id = %s",
            (event_id,)
        )
        return result > 0