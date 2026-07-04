"""
User Repository
===============
Data access layer untuk users.
"""

from .base_repository import BaseRepository
from backend.models import UserModel
from typing import Optional, List, Dict


class UserRepository(BaseRepository):
    """Repository untuk tabel users."""

    TABLE = "users"

    @classmethod
    def get_by_email(cls, email: str) -> Optional[Dict]:
        """Ambil user by email."""
        return UserModel.get_by_email(email)

    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional[Dict]:
        """Autentikasi user."""
        return UserModel.authenticate(email, password)

    @classmethod
    def create(cls, name: str, email: str, password: str, 
               role: str = 'participant', **kwargs) -> Optional[Dict]:
        """Buat user baru."""
        return UserModel.create(name, email, password, role, **kwargs)

    @classmethod
    def update(cls, user_id: str, **kwargs) -> Optional[Dict]:
        """Update user."""
        return UserModel.update(user_id, **kwargs)

    @classmethod
    def list_by_role(cls, role: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """List user by role."""
        return UserModel.list_all(role=role, limit=limit, offset=offset)