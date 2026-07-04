"""
Ticket Service
==============
Business logic untuk ticket management.
"""

from backend.repositories import TicketRepository
from backend.models import TicketModel
from typing import Optional, List, Dict


class TicketService:
    """Service untuk tiket."""

    @staticmethod
    def create_ticket(event_id: str, **kwargs) -> Dict:
        """Buat tiket baru."""
        ticket = TicketModel.create(event_id=event_id, **kwargs)
        if ticket:
            return {"success": True, "ticket": ticket}
        return {"success": False, "message": "Gagal membuat tiket"}

    @staticmethod
    def get_event_tickets(event_id: str) -> List[Dict]:
        """Ambil tiket per event."""
        return TicketRepository.get_by_event(event_id)

    @staticmethod
    def check_availability(ticket_id: str) -> Dict:
        """Cek ketersediaan tiket."""
        result = TicketRepository.check_availability(ticket_id)
        if result:
            return {
                "available": result['available'],
                "remaining": result['remaining'],
                "price": result['price'],
                "max_per_order": result['max_per_order']
            }
        return {"available": False, "message": "Tiket tidak ditemukan"}

    @staticmethod
    def get_ticket_stats(event_id: str) -> Optional[Dict]:
        """Get statistik tiket."""
        return TicketRepository.get_stats_by_event(event_id)