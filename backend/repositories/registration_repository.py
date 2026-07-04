"""
Registration Repository
=======================
Data access layer untuk registrations.
"""

from .base_repository import BaseRepository
from backend.models import RegistrationModel
from typing import Optional, List, Dict


class RegistrationRepository(BaseRepository):
    """Repository untuk tabel registrations."""

    TABLE = "registrations"

    @classmethod
    def create(cls, user_id: str, ticket_id: str, quantity: int = 1, 
               payment_method: str = None) -> Optional[Dict]:
        """Buat registrasi."""
        return RegistrationModel.create(user_id, ticket_id, quantity, payment_method)

    @classmethod
    def get_by_user(cls, user_id: str, status: str = None) -> List[Dict]:
        """Ambil registrasi by user."""
        return RegistrationModel.get_by_user(user_id, status)

    @classmethod
    def get_event_registrations(cls, event_id: str) -> List[Dict]:
        """Ambil registrasi by event."""
        return RegistrationModel.get_event_registrations(event_id)

    @classmethod
    def update_status(cls, registration_id: str, status: str) -> Optional[Dict]:
        """Update status."""
        return RegistrationModel.update_status(registration_id, status)

    @classmethod
    def cancel(cls, registration_id: str) -> bool:
        """Cancel registrasi."""
        return RegistrationModel.cancel(registration_id)

    @classmethod
    def check_in(cls, registration_id: str, checked_in_by: str) -> Optional[Dict]:
        """Check-in."""
        return RegistrationModel.check_in(registration_id, checked_in_by)