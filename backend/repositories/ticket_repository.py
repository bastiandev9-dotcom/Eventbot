"""
Ticket Repository
=================
Data access layer untuk tickets.
"""

from .base_repository import BaseRepository
from backend.models import TicketModel
from typing import Optional, List, Dict


class TicketRepository(BaseRepository):
    """Repository untuk tabel tickets."""

    TABLE = "tickets"

    @classmethod
    def get_by_event(cls, event_id: str) -> List[Dict]:
        """Ambil tiket by event."""
        return TicketModel.get_by_event(event_id)

    @classmethod
    def check_availability(cls, ticket_id: str) -> Optional[Dict]:
        """Cek ketersediaan tiket."""
        return TicketModel.check_availability(ticket_id)

    @classmethod
    def get_stats_by_event(cls, event_id: str) -> Optional[Dict]:
        """Get statistik tiket."""
        return TicketModel.get_stats_by_event(event_id)