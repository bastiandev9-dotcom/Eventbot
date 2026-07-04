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
            SELECT id, title, slug, image_url, view_count, start_date, location
            FROM events
            WHERE deleted_at IS NULL AND is_published = TRUE
              AND status IN ('upcoming', 'ongoing')
            ORDER BY view_count DESC
            LIMIT %s;
        """
        return execute_query(sql, (limit,), fetch_all=True) or []

    @staticmethod
    def get_upcoming_events(limit: int = 10) -> List[Dict]:
        """Get event yang akan datang."""
        return EventModel.search(status='upcoming', limit=limit)