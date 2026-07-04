"""
Event Repository
================
Data access layer untuk events.
"""

from .base_repository import BaseRepository
from backend.models import EventModel
from typing import Optional, List, Dict


class EventRepository(BaseRepository):
    """Repository untuk tabel events."""

    TABLE = "events"

    @classmethod
    def get_by_slug(cls, slug: str) -> Optional[Dict]:
        """Ambil event by slug."""
        return EventModel.get_by_slug(slug)

    @classmethod
    def create(cls, **kwargs) -> Optional[Dict]:
        """Buat event baru."""
        return EventModel.create(**kwargs)

    @classmethod
    def search(cls, **kwargs) -> List[Dict]:
        """Cari event dengan filter."""
        return EventModel.search(**kwargs)

    @classmethod
    def list_by_organizer(cls, organizer_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """List event by organizer."""
        return EventModel.list_by_organizer(organizer_id, limit, offset)

    @classmethod
    def get_recommended(cls, event_id: str, limit: int = 3) -> List[Dict]:
        """Get rekomendasi event."""
        return EventModel.get_recommended(event_id, limit)