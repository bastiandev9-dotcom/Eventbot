"""
Event Service
=============
Business logic untuk event management.
"""

from backend.repositories import EventRepository
from backend.models import EventModel
from typing import Optional, List, Dict


class EventService:
    """Service untuk event."""

    @staticmethod
    def create_event(organizer_id: str, **kwargs) -> Dict:
        """Buat event baru."""
        event = EventRepository.create(organizer_id=organizer_id, **kwargs)
        if event:
            return {"success": True, "event": event}
        return {"success": False, "message": "Gagal membuat event"}

    @staticmethod
    def get_event_detail(event_id: str) -> Optional[Dict]:
        """Ambil detail event."""
        return EventRepository.get_by_id(event_id)

    @staticmethod
    def search_events(**filters) -> List[Dict]:
        """Cari event."""
        return EventRepository.search(**filters)

    @staticmethod
    def update_event(event_id: str, **kwargs) -> Dict:
        """Update event."""
        event = EventModel.update(event_id, **kwargs)
        if event:
            return {"success": True, "event": event}
        return {"success": False, "message": "Gagal update event"}

    @staticmethod
    def delete_event(event_id: str) -> Dict:
        """Hapus event."""
        success = EventModel.delete(event_id)
        return {"success": success, "message": "Event dihapus" if success else "Gagal menghapus event"}

    @staticmethod
    def get_organizer_events(organizer_id: str) -> List[Dict]:
        """Ambil event milik organizer."""
        return EventRepository.list_by_organizer(organizer_id)

    @staticmethod
    def get_recommendations(event_id: str, limit: int = 3) -> List[Dict]:
        """Get rekomendasi event."""
        return EventRepository.get_recommended(event_id, limit)