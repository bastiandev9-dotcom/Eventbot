"""
EventBot Repositories
=====================
Data Access Layer - Abstraksi CRUD untuk setiap entitas.
"""

from .user_repository import UserRepository
from .event_repository import EventRepository
from .ticket_repository import TicketRepository
from .registration_repository import RegistrationRepository

__all__ = [
    'UserRepository',
    'EventRepository', 
    'TicketRepository',
    'RegistrationRepository',
]