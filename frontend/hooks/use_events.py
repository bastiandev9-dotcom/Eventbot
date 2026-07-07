"""
use_events Hook
===============
Hook untuk mengambil dan mengelola data event dari backend.
Mendukung caching sederhana via st.session_state untuk mengurangi API calls.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Tuple

from utils.session_manager import SessionManager
from utils.api_client import APIClient, APIError


# ── Cache TTL (detik) ─────────────────────────────────────
_CACHE_TTL = 10  # 10 detik

import time


def _is_cache_valid(cache_key: str) -> bool:
    ts_key = f"{cache_key}_ts"
    ts = st.session_state.get(ts_key, 0)
    return (time.time() - ts) < _CACHE_TTL


def _set_cache(cache_key: str, data: Any) -> None:
    st.session_state[cache_key] = data
    st.session_state[f"{cache_key}_ts"] = time.time()


def _get_cache(cache_key: str) -> Optional[Any]:
    if _is_cache_valid(cache_key):
        return st.session_state.get(cache_key)
    return None


def use_events() -> Dict[str, Any]:
    """
    Hook manajemen data event.

    Returns:
        Dict berisi fungsi-fungsi untuk berinteraksi dengan event API.
    """
    SessionManager.init()
    token = SessionManager.get_token()

    def get_client(require_auth: bool = False) -> APIClient:
        if require_auth and not token:
            raise APIError("Login diperlukan untuk operasi ini.", 401)
        return APIClient(token=token)

    def fetch_events(
        q: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,   # None = semua status
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
        use_cache: bool = True,
    ) -> Tuple[List[Dict], int, Optional[str]]:
        """
        Ambil daftar event dari backend.

        Returns:
            (list_events, total_count, error_message)
        """
        # Buat cache key unik berdasarkan filter
        cache_key = f"events_{q}_{location}_{category}_{start_date}_{end_date}_{status}_{min_price}_{max_price}_{page}"
        if use_cache:
            cached = _get_cache(cache_key)
            if cached is not None:
                return cached["data"], cached["count"], None

        try:
            client = get_client()
            result = client.get_events(
                q=q,
                location=location,
                category=category,
                start_date=start_date,
                end_date=end_date,
                status=status,
                min_price=min_price,
                max_price=max_price,
                page=page,
                page_size=page_size,
            )
            events = result.get("data", [])
            count = result.get("count", len(events))
            _set_cache(cache_key, {"data": events, "count": count})
            return events, count, None
        except APIError as e:
            return [], 0, e.message
        except Exception as e:
            return [], 0, "Gagal memuat event. Periksa koneksi ke server."

    def fetch_event(event_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Ambil detail satu event beserta tiketnya.

        Returns:
            (event_dict, error_message)
        """
        cache_key = f"event_detail_{event_id}"
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached, None

        try:
            client = get_client()

            # Ambil detail event
            result = client.get_event(event_id)

            # Backend bisa return {"data": {...}} atau langsung {...}
            if isinstance(result, dict) and "data" in result:
                event = result.get("data")
            else:
                event = result

            if not event:
                return None, "Event tidak ditemukan."

            # Jika tiket belum ada dalam response event, fetch terpisah
            if not event.get("tickets"):
                try:
                    tickets = client.get_event_tickets(event_id)
                    event["tickets"] = tickets if isinstance(tickets, list) else []
                except Exception:
                    event["tickets"] = []

            _set_cache(cache_key, event)
            return event, None

        except APIError as e:
            if e.status_code == 404:
                return None, "Event tidak ditemukan."
            return None, e.message
        except Exception:
            return None, "Gagal memuat detail event."

    def fetch_trending(limit: int = 5) -> Tuple[List[Dict], Optional[str]]:
        """Ambil event trending."""
        cache_key = f"events_trending_{limit}"
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached, None
        try:
            client = get_client()
            result = client.get_trending_events(limit=limit)
            events = result.get("data", [])
            _set_cache(cache_key, events)
            return events, None
        except APIError as e:
            return [], e.message
        except Exception:
            return [], "Gagal memuat event trending."

    def fetch_upcoming(limit: int = 10) -> Tuple[List[Dict], Optional[str]]:
        """Ambil event yang akan segera berlangsung."""
        cache_key = f"events_upcoming_{limit}"
        cached = _get_cache(cache_key)
        if cached is not None:
            return cached, None
        try:
            client = get_client()
            result = client.get_upcoming_events(limit=limit)
            events = result.get("data", [])
            _set_cache(cache_key, events)
            return events, None
        except APIError as e:
            return [], e.message
        except Exception:
            return [], "Gagal memuat upcoming events."

    def fetch_similar(event_id: str, limit: int = 3) -> Tuple[List[Dict], Optional[str]]:
        """Ambil event serupa."""
        try:
            client = get_client()
            result = client.get_similar_events(event_id=event_id, limit=limit)
            return result.get("data", []), None
        except APIError as e:
            return [], e.message
        except Exception:
            return [], "Gagal memuat rekomendasi."

    def create_event(data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Buat event baru. Requires login sebagai admin.

        Returns:
            (success, message, event_data)
        """
        try:
            client = get_client(require_auth=True)
            result = client.create_event(data)
            event = result.get("data")
            # Invalidate cache
            _invalidate_event_caches()
            return True, "Event berhasil dibuat!", event
        except APIError as e:
            if e.status_code == 401:
                return False, "Silakan login terlebih dahulu.", None
            if e.status_code == 403:
                return False, "Hanya admin yang bisa membuat event.", None
            return False, e.message, None
        except Exception:
            return False, "Gagal membuat event.", None

    def update_event(event_id: str, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """Update event. Requires login sebagai admin."""
        try:
            client = get_client(require_auth=True)
            result = client.update_event(event_id, data)
            event = result.get("data")
            # Invalidate cache detail
            if f"event_detail_{event_id}" in st.session_state:
                del st.session_state[f"event_detail_{event_id}"]
            _invalidate_event_caches()
            return True, "Event berhasil diperbarui!", event
        except APIError as e:
            return False, e.message, None
        except Exception:
            return False, "Gagal memperbarui event.", None

    def delete_event(event_id: str) -> Tuple[bool, str]:
        """Hapus event. Requires login sebagai admin.

        Penting: Fungsi ini TIDAK boleh mengubah auth session (token/login state).
        Semua exception ditangkap dan dikembalikan sebagai (False, pesan_error).
        """
        try:
            client = get_client(require_auth=True)
        except APIError as e:
            # Token tidak ada — user memang belum login, jangan logout paksa
            return False, "Login diperlukan untuk menghapus event."
        except Exception:
            return False, "Gagal terhubung ke layanan autentikasi."

        try:
            client.delete_event(event_id)
            # Invalidate cache HANYA setelah berhasil
            _invalidate_event_caches()
            return True, "Event berhasil dihapus."
        except APIError as e:
            if e.status_code == 401:
                # Token expired — jangan paksa logout di sini, biarkan user sadar sendiri
                return False, "Sesi Anda telah berakhir. Silakan refresh halaman."
            if e.status_code == 403:
                return False, "Anda tidak memiliki izin untuk menghapus event ini."
            if e.status_code == 404:
                # Event sudah tidak ada — anggap berhasil dihapus, bersihkan cache
                _invalidate_event_caches()
                return True, "Event sudah dihapus sebelumnya."
            return False, f"Gagal menghapus event: {e.message}"
        except Exception as e:
            # Jangan crash, jangan logout — kembalikan pesan error yang jelas
            return False, "Gagal menghapus event. Periksa koneksi ke server."

    def fetch_my_events() -> Tuple[List[Dict], Optional[str]]:
        """Ambil event yang dibuat oleh admin yang sedang login."""
        try:
            client = get_client(require_auth=True)
            result = client.get_my_events()
            return result.get("data", []), None
        except APIError as e:
            return [], e.message
        except Exception:
            return [], "Gagal memuat event Anda."

    def register_to_event(event_id: str, ticket_id: str) -> Tuple[bool, str]:
        """Daftar ke sebuah event (beli tiket)."""
        try:
            client = get_client(require_auth=True)
            result = client.register_event(event_id=event_id, ticket_id=ticket_id)
            return True, "Berhasil mendaftar event! 🎉"
        except APIError as e:
            if e.status_code == 401:
                return False, "Silakan login terlebih dahulu."
            if e.status_code == 409:
                return False, "Anda sudah terdaftar di event ini."
            return False, e.message
        except Exception:
            return False, "Gagal mendaftar event."

    def _invalidate_event_caches() -> None:
        """Hapus semua cache event dari session state."""
        keys_to_delete = [
            k for k in st.session_state.keys()
            if k.startswith("events_") or k.startswith("event_detail_")
        ]
        for k in keys_to_delete:
            del st.session_state[k]

    return {
        "fetch_events": fetch_events,
        "fetch_event": fetch_event,
        "fetch_trending": fetch_trending,
        "fetch_upcoming": fetch_upcoming,
        "fetch_similar": fetch_similar,
        "create_event": create_event,
        "update_event": update_event,
        "delete_event": delete_event,
        "fetch_my_events": fetch_my_events,
        "register_to_event": register_to_event,
    }
