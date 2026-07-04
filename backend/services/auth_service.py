"""
Auth Service
============
Business logic untuk autentikasi & session management.
"""

from backend.repositories import UserRepository
from backend.config import create_access_token, generate_session_token
from backend.config.security import hash_password
from datetime import timedelta
from typing import Optional, Dict


class AuthService:
    """Service untuk autentikasi."""

    @staticmethod
    def register(name: str, email: str, password: str, 
                 role: str = 'participant', **kwargs) -> Dict:
        """Register user baru."""
        # Cek email sudah ada
        existing = UserRepository.get_by_email(email)
        if existing:
            return {"success": False, "message": "Email sudah terdaftar"}

        # Buat user
        user = UserRepository.create(name, email, password, role, **kwargs)
        if user:
            return {"success": True, "user": user, "message": "Registrasi berhasil"}
        return {"success": False, "message": "Gagal membuat akun"}

    @staticmethod
    def login(email: str, password: str) -> Dict:
        """Login user."""
        user = UserRepository.authenticate(email, password)
        if not user:
            return {"success": False, "message": "Email atau password salah"}

        # Buat JWT token
        token_data = {
            "sub": str(user['id']),
            "email": user['email'],
            "role": user['role']
        }
        access_token = create_access_token(token_data, expires_delta=timedelta(hours=24))

        return {
            "success": True,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role']
            },
            "access_token": access_token
        }

    @staticmethod
    def get_current_user(user_id: str) -> Optional[Dict]:
        """Ambil data user yang sedang login."""
        return UserRepository.get_by_id(user_id)

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> Dict:
        """Ganti password."""
        from backend.models import UserModel

        user = UserRepository.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "User tidak ditemukan"}

        # Verify old password
        from backend.config.security import verify_password
        if not verify_password(old_password, user.get('password_hash', '')):
            return {"success": False, "message": "Password lama salah"}

        # Update password
        success = UserModel.update_password(user_id, new_password)
        return {"success": success, "message": "Password berhasil diubah" if success else "Gagal mengubah password"}