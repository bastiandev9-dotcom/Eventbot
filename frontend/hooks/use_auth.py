"""
use_auth Hook
=============
Hook untuk manajemen state autentikasi.
Menyederhanakan operasi login, register, logout, dan cek auth.
"""

import streamlit as st
from typing import Optional, Dict, Any, Tuple

from utils.session_manager import SessionManager
from utils.api_client import APIClient, APIError


def use_auth() -> Dict[str, Any]:
    """
    Hook autentikasi EventBot.

    Returns:
        Dict berisi:
        - is_logged_in: bool
        - user: Dict user atau None
        - role: str ('guest', 'participant', 'admin')
        - token: str atau None
        - login(email, password) -> (success: bool, message: str)
        - register(name, email, password, role, phone, bio) -> (bool, str)
        - logout() -> None
        - refresh_profile() -> bool
        - require_login(redirect_page) -> bool  (cek akses)
        - require_role(*roles) -> bool
    """
    SessionManager.init()

    def login(email: str, password: str) -> Tuple[bool, str]:
        """
        Login user ke backend.

        Returns:
            (True, "Login berhasil") atau (False, "pesan error")
        """
        if not email or not password:
            return False, "Email dan password wajib diisi."

        client = APIClient()
        try:
            result = client.login(email=email, password=password)
            if result.get("success"):
                token = result.get("access_token", "")
                user = result.get("user", {})
                SessionManager.login(user=user, token=token)
                return True, f"Selamat datang, {user.get('name', 'User')}! 👋"
            return False, result.get("message", "Login gagal.")
        except APIError as e:
            if e.status_code == 401:
                return False, "Email atau password salah."
            return False, f"Login gagal: {e.message}"
        except Exception as e:
            return False, "Tidak dapat terhubung ke server. Pastikan backend berjalan."

    def register(
        name: str,
        email: str,
        password: str,
        role: str = "participant",
        phone: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Daftarkan akun baru.

        Returns:
            (True, "Registrasi berhasil") atau (False, "pesan error")
        """
        # Validasi dasar di sisi frontend
        if not all([name, email, password]):
            return False, "Nama, email, dan password wajib diisi."
        if len(password) < 6:
            return False, "Password minimal 6 karakter."
        if "@" not in email:
            return False, "Format email tidak valid."

        client = APIClient()
        try:
            result = client.register(
                name=name,
                email=email,
                password=password,
                role=role,
                phone=phone,
                bio=bio,
            )
            if result.get("success"):
                return True, "Registrasi berhasil! Silakan login."
            return False, result.get("message", "Registrasi gagal.")
        except APIError as e:
            if e.status_code == 400:
                return False, e.message
            return False, f"Registrasi gagal: {e.message}"
        except Exception:
            return False, "Tidak dapat terhubung ke server."

    def logout() -> None:
        """Logout user: hapus sesi lokal dan panggil backend logout."""
        token = SessionManager.get_token()
        if token:
            try:
                client = APIClient(token=token)
                client.logout()
            except Exception:
                pass  # Lanjut logout lokal meski backend error
        SessionManager.logout()

    def refresh_profile() -> bool:
        """
        Refresh data profil dari backend menggunakan token yang tersimpan.

        Returns:
            True jika berhasil, False jika token tidak valid.
        """
        token = SessionManager.get_token()
        if not token:
            return False
        try:
            client = APIClient(token=token)
            result = client.get_profile()
            if result.get("success"):
                user = result.get("user", {})
                # Update user data di session state
                SessionManager.login(user=user, token=token)
                return True
            return False
        except APIError as e:
            if e.status_code in (401, 403):
                SessionManager.logout()
            return False
        except Exception:
            return False

    def require_login(redirect_message: str = "Silakan login untuk mengakses halaman ini.") -> bool:
        """
        Cek apakah user sudah login.
        Tampilkan warning jika belum.

        Returns:
            True jika sudah login, False jika belum.
        """
        if not SessionManager.is_logged_in():
            st.warning(f"🔐 {redirect_message}")
            if st.button("Login Sekarang", key="btn_require_login"):
                st.session_state["current_page"] = "Login"
                st.rerun()
            return False
        return True

    def require_role(*allowed_roles: str) -> bool:
        """
        Cek apakah user memiliki role yang diizinkan.

        Args:
            *allowed_roles: Role yang diizinkan, contoh: 'admin'

        Returns:
            True jika role cocok, False jika tidak.
        """
        if not SessionManager.is_logged_in():
            st.warning("🔐 Silakan login terlebih dahulu.")
            return False

        role = SessionManager.get_role()
        if role not in allowed_roles:
            st.error(f"⛔ Akses ditolak. Halaman ini hanya untuk: {', '.join(allowed_roles)}.")
            return False
        return True

    return {
        "is_logged_in": SessionManager.is_logged_in(),
        "user": SessionManager.get_user(),
        "role": SessionManager.get_role(),
        "token": SessionManager.get_token(),
        "is_admin": SessionManager.is_admin(),
        "is_participant": SessionManager.is_participant(),
        "login": login,
        "register": register,
        "logout": logout,
        "refresh_profile": refresh_profile,
        "require_login": require_login,
        "require_role": require_role,
    }
