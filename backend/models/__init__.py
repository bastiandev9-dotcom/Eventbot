"""
EventBot Models Package
========================
Data models dengan CRUD operations untuk setiap tabel.
"""

from .user import UserModel
from .event import EventModel
from .ticket import TicketModel
from .registration import RegistrationModel
from .category import CategoryModel
from .chat_history import ChatSessionModel, ChatMessageModel
from .knowledge_base import KnowledgeBaseModel
from .system_settings import SystemSettingsModel

__all__ = [
    'UserModel',
    'EventModel',
    'TicketModel',
    'RegistrationModel',
    'CategoryModel',
    'ChatSessionModel',
    'ChatMessageModel',
    'KnowledgeBaseModel',
    'SystemSettingsModel',
]