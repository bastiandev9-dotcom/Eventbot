"""
Registration Service
====================
Business logic untuk booking & registration.
"""

from backend.repositories import RegistrationRepository
from backend.models import RegistrationModel
from typing import Optional, List, Dict


class RegistrationService:
    """Service untuk registrasi."""

    @staticmethod
    def book_ticket(user_id: str, ticket_id: str, quantity: int = 1, 
                    payment_method: str = None) -> Dict:
        """Booking tiket."""
        result = RegistrationRepository.create(user_id, ticket_id, quantity, payment_method)

        if result and result.get('success'):
            return {
                "success": True,
                "registration_id": result['registration_id'],
                "total_price": result['total_price'],
                "message": result['message']
            }
        return {
            "success": False,
            "message": result.get('message', 'Gagal melakukan booking') if result else 'Gagal melakukan booking'
        }

    @staticmethod
    def get_user_registrations(user_id: str, status: str = None) -> List[Dict]:
        """Ambil registrasi user."""
        return RegistrationRepository.get_by_user(user_id, status)

    @staticmethod
    def cancel_registration(registration_id: str) -> Dict:
        """Cancel registrasi."""
        success = RegistrationRepository.cancel(registration_id)
        return {"success": success, "message": "Registrasi dibatalkan" if success else "Gagal membatalkan"}

    @staticmethod
    def confirm_payment(registration_id: str) -> Dict:
        """Konfirmasi pembayaran."""
        result = RegistrationRepository.update_status(registration_id, 'confirmed')
        return {"success": bool(result), "registration": result}

    @staticmethod
    def check_in(registration_id: str, checked_in_by: str) -> Dict:
        """Check-in peserta."""
        result = RegistrationRepository.check_in(registration_id, checked_in_by)
        return {"success": bool(result), "check_in": result}