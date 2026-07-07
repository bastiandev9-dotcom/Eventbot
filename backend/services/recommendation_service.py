"""
Recommendation Service
======================
Business logic untuk rekomendasi event.
"""

from backend.repositories import EventRepository
from backend.models import EventModel
from typing import List, Dict


class RecommendationService:
    """Service untuk rekomendasi event."""

    @staticmethod
    def get_similar_events(event_id: str, limit: int = 3) -> List[Dict]:
        """Get event serupa berdasarkan kategori."""
        return EventRepository.get_recommended(event_id, limit)

    @staticmethod
    def get_trending_events(limit: int = 5) -> List[Dict]:
        """Get event trending (banyak view)."""
        from backend.config import execute_query

        sql = """
            SELECT
                e.id, e.title, e.slug, e.image_url, e.view_count,
                e.start_date, e.location, e.status, e.capacity, e.short_description,
                MIN(t.price) AS min_price,
                COALESCE(MAX(reg.registered_count), 0) AS registered_count
            FROM events e
            LEFT JOIN tickets t ON e.id = t.event_id AND t.deleted_at IS NULL
            LEFT JOIN (
                SELECT event_id, COUNT(*) AS registered_count
                FROM registrations
                WHERE status = 'confirmed'
                GROUP BY event_id
            ) reg ON reg.event_id = e.id
            WHERE e.deleted_at IS NULL AND e.is_published = TRUE
              AND e.status IN ('upcoming', 'ongoing')
            GROUP BY e.id, e.title, e.slug, e.image_url, e.view_count,
                     e.start_date, e.location, e.status, e.capacity, e.short_description
            ORDER BY e.view_count DESC
            LIMIT %s;
        """
        return execute_query(sql, (limit,), fetch_all=True) or []

    @staticmethod
    def get_upcoming_events(limit: int = 10) -> List[Dict]:
        """Get event yang akan datang."""
        return EventModel.search(status='upcoming', limit=limit)