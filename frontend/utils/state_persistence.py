"""
State Persistence
=================
Menyimpan dan memulihkan state sesi ke/dari file lokal (JSON).
Berguna agar user tidak perlu login ulang setiap refresh halaman.

Catatan: Ini adalah persistence sederhana berbasis file lokal.
Untuk produksi, pertimbangkan menggunakan browser localStorage via
streamlit-js-eval atau database sesi server-side.
"""

import json
import os
import time
from typing import Optional, Dict, Any
from pathlib import Path


# ── Config ────────────────────────────────────────────────
_STATE_DIR = Path(__file__).parent.parent / ".sessions"
_STATE_TTL = 60 * 60 * 24 * 7  # 7 hari dalam detik


class StatePersistence:
    """
    Simpan/restore minimal session state ke file JSON lokal.
    Hanya menyimpan data non-sensitif seperti theme preference
    dan session token (bukan password).
    """

    @staticmethod
    def _ensure_dir() -> None:
        """Buat direktori session jika belum ada."""
        _STATE_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_file_path(session_id: str) -> Path:
        # Sanitasi session_id agar aman sebagai nama file
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return _STATE_DIR / f"{safe_id}.json"

    @classmethod
    def save(cls, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Simpan data state ke file JSON.

        Args:
            session_id: ID unik sesi (misal: user_id atau UUID)
            data: Dict berisi state yang ingin disimpan.
                  JANGAN masukkan password atau data sensitif.

        Returns:
            True jika berhasil, False jika gagal.
        """
        try:
            cls._ensure_dir()
            payload = {
                "saved_at": time.time(),
                "data": data,
            }
            file_path = cls._get_file_path(session_id)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @classmethod
    def load(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Muat data state dari file JSON.

        Returns:
            Dict berisi state, atau None jika tidak ada / expired / corrupt.
        """
        try:
            file_path = cls._get_file_path(session_id)
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            # Cek expired
            saved_at = payload.get("saved_at", 0)
            if time.time() - saved_at > _STATE_TTL:
                cls.delete(session_id)
                return None

            return payload.get("data")
        except Exception:
            return None

    @classmethod
    def delete(cls, session_id: str) -> bool:
        """Hapus file state untuk session_id tertentu."""
        try:
            file_path = cls._get_file_path(session_id)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception:
            return False

    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Hapus semua file sesi yang sudah expired.

        Returns:
            Jumlah file yang dihapus.
        """
        count = 0
        try:
            cls._ensure_dir()
            for file_path in _STATE_DIR.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    saved_at = payload.get("saved_at", 0)
                    if time.time() - saved_at > _STATE_TTL:
                        file_path.unlink()
                        count += 1
                except Exception:
                    # File corrupt, hapus
                    try:
                        file_path.unlink()
                        count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return count

    # ── Convenience: Theme ────────────────────────────────

    @classmethod
    def save_theme(cls, user_id: str, theme: str) -> bool:
        """Shortcut: simpan preferensi tema user."""
        existing = cls.load(f"theme_{user_id}") or {}
        existing["theme"] = theme
        return cls.save(f"theme_{user_id}", existing)

    @classmethod
    def load_theme(cls, user_id: str) -> str:
        """Shortcut: muat preferensi tema user."""
        data = cls.load(f"theme_{user_id}")
        if data and "theme" in data:
            return data["theme"]
        return "dark"  # default

    # ── Convenience: Chat Session Token ──────────────────

    @classmethod
    def save_chat_token(cls, identifier: str, token: str) -> bool:
        """Simpan chat session token agar percakapan tidak hilang saat refresh."""
        return cls.save(f"chat_{identifier}", {"chat_token": token, "ts": time.time()})

    @classmethod
    def load_chat_token(cls, identifier: str) -> Optional[str]:
        """Muat chat session token."""
        data = cls.load(f"chat_{identifier}")
        return data.get("chat_token") if data else None
