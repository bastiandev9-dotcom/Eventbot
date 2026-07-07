"""
API Client
==========
HTTP client untuk berkomunikasi dengan backend EventBot (FastAPI).
Base URL: http://localhost:8000/api/v1
"""

import requests
from typing import Optional, Dict, Any, List
from requests.exceptions import ConnectionError, Timeout, RequestException

# ── Config ────────────────────────────────────────────────
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10  # detik


class APIError(Exception):
    """Exception khusus untuk error dari API."""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class APIClient:
    """
    HTTP client yang meng-wrap requests ke backend EventBot.

    Contoh penggunaan:
        client = APIClient(token="Bearer eyJ...")
        events = client.get_events(q="teknologi", location="Jakarta")
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse response dan raise APIError jika ada error."""
        try:
            data = response.json()
        except ValueError:
            raise APIError(f"Response bukan JSON: {response.text}", response.status_code)

        if not response.ok:
            detail = data.get("detail", data.get("message", "Terjadi kesalahan"))
            raise APIError(detail, response.status_code)

        return data

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            resp = self.session.get(f"{BASE_URL}{endpoint}", params=params, timeout=TIMEOUT)
            return self._handle_response(resp)
        except ConnectionError:
            raise APIError("Tidak dapat terhubung ke server. Pastikan backend sudah berjalan.")
        except Timeout:
            raise APIError("Request timeout. Coba lagi beberapa saat.")
        except RequestException as e:
            raise APIError(f"Request error: {e}")

    def _post(self, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            resp = self.session.post(f"{BASE_URL}{endpoint}", json=json, timeout=TIMEOUT)
            return self._handle_response(resp)
        except ConnectionError:
            raise APIError("Tidak dapat terhubung ke server. Pastikan backend sudah berjalan.")
        except Timeout:
            raise APIError("Request timeout. Coba lagi beberapa saat.")
        except RequestException as e:
            raise APIError(f"Request error: {e}")

    def _put(self, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            resp = self.session.put(f"{BASE_URL}{endpoint}", json=json, timeout=TIMEOUT)
            return self._handle_response(resp)
        except ConnectionError:
            raise APIError("Tidak dapat terhubung ke server.")
        except Timeout:
            raise APIError("Request timeout.")
        except RequestException as e:
            raise APIError(f"Request error: {e}")

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        try:
            resp = self.session.delete(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            return self._handle_response(resp)
        except ConnectionError:
            raise APIError("Tidak dapat terhubung ke server.")
        except Timeout:
            raise APIError("Request timeout.")
        except RequestException as e:
            raise APIError(f"Request error: {e}")

    # ── Auth ──────────────────────────────────────────────

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user, kembalikan access_token dan data user."""
        return self._post("/auth/login", {"email": email, "password": password})

    def register(
        self,
        name: str,
        email: str,
        password: str,
        role: str = "participant",
        phone: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Daftarkan akun baru."""
        payload: Dict[str, Any] = {
            "name": name,
            "email": email,
            "password": password,
            "role": role,
        }
        if phone:
            payload["phone"] = phone
        if bio:
            payload["bio"] = bio
        return self._post("/auth/register", payload)

    def get_profile(self) -> Dict[str, Any]:
        """Ambil profil user yang sedang login."""
        return self._get("/auth/me")

    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        return self._put("/auth/change-password", {
            "old_password": old_password,
            "new_password": new_password,
        })

    def logout(self) -> Dict[str, Any]:
        return self._post("/auth/logout")

    # ── Events ────────────────────────────────────────────

    def get_events(
        self,
        q: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,   # None = semua status (tidak difilter)
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Ambil daftar event dengan filter & pagination."""
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }
        # Hanya kirim status jika ada nilai (string non-kosong)
        if status:
            params["status"] = status
        if q:
            params["q"] = q
        if location:
            params["location"] = location
        if category:
            params["category"] = category
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        return self._get("/events/", params)

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """Detail sebuah event."""
        return self._get(f"/events/{event_id}")

    def get_trending_events(self, limit: int = 5) -> Dict[str, Any]:
        return self._get("/events/trending", {"limit": limit})

    def get_upcoming_events(self, limit: int = 10) -> Dict[str, Any]:
        return self._get("/events/upcoming", {"limit": limit})

    def get_similar_events(self, event_id: str, limit: int = 3) -> Dict[str, Any]:
        return self._get(f"/events/{event_id}/recommendations", {"limit": limit})

    def create_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/events/", data)

    def update_event(self, event_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._put(f"/events/{event_id}", data)

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        return self._delete(f"/events/{event_id}")

    def get_my_events(self) -> Dict[str, Any]:
        """Event yang dibuat oleh admin yang sedang login."""
        return self._get("/events/organizer/my-events")

    # ── Chatbot ───────────────────────────────────────────

    def send_message(
        self,
        message: str,
        session_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Kirim pesan ke chatbot dan terima respons NLP."""
        payload: Dict[str, Any] = {"message": message}
        if session_token:
            payload["session_token"] = session_token
        return self._post("/chatbot/message", payload)

    def get_chat_history(self, session_token: str) -> Dict[str, Any]:
        return self._get("/chatbot/history", {"session_token": session_token})

    def get_intents(self) -> Dict[str, Any]:
        return self._get("/chatbot/intents")

    # ── Tickets ───────────────────────────────────────────

    def get_tickets(self, event_id: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if event_id:
            params["event_id"] = event_id
        return self._get("/tickets/", params)

    def get_event_tickets(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Ambil daftar tiket milik sebuah event.

        Returns:
            List tiket langsung (bukan dict wrapper).
        """
        try:
            result = self._get(f"/events/{event_id}/tickets")
            # Backend bisa return {'data': [...]} atau langsung [...]
            if isinstance(result, list):
                return result
            return result.get("data", result.get("tickets", []))
        except APIError:
            # Fallback: gunakan endpoint tickets umum dengan filter event_id
            result = self._get("/tickets/", {"event_id": event_id})
            if isinstance(result, list):
                return result
            return result.get("data", [])

    def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        return self._get(f"/tickets/{ticket_id}")

    def create_ticket(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/tickets/", data)

    def update_ticket(self, ticket_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._put(f"/tickets/{ticket_id}", data)

    def delete_ticket(self, ticket_id: str) -> Dict[str, Any]:
        return self._delete(f"/tickets/{ticket_id}")

    # ── Registrations ─────────────────────────────────────

    def register_event(self, event_id: str, ticket_id: str) -> Dict[str, Any]:
        return self._post("/registrations/", {
            "event_id": event_id,
            "ticket_id": ticket_id,
        })

    def book_ticket(
        self,
        ticket_id: str,
        quantity: int = 1,
        payment_method: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Beli tiket event via endpoint /registrations/book.

        Args:
            ticket_id: UUID tiket yang ingin dibeli
            quantity: Jumlah tiket (1-20)
            payment_method: Metode bayar ('transfer_bank', 'e_wallet', None = gratis)
            event_id: UUID event (opsional, beberapa backend memerlukannya)

        Returns:
            Dict berisi registration_id, total_price, message
        """
        payload: Dict[str, Any] = {
            "ticket_id": ticket_id,
            "quantity": quantity,
        }
        if payment_method:
            payload["payment_method"] = payment_method
        if event_id:
            payload["event_id"] = event_id
        return self._post("/registrations/book", payload)

    def get_my_registrations(self) -> Dict[str, Any]:
        return self._get("/registrations/my")

    def get_registrations(self, event_id: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if event_id:
            params["event_id"] = event_id
        return self._get("/registrations/", params)

    def get_pending_registrations(self, event_id: Optional[str] = None) -> Dict[str, Any]:
        """Ambil semua registrasi berstatus pending (untuk admin)."""
        params = {"status": "pending"}
        if event_id:
            params["event_id"] = event_id
        return self._get("/registrations/", params)

    def confirm_payment(self, registration_id: str) -> Dict[str, Any]:
        """Konfirmasi pembayaran registrasi (admin only)."""
        return self._post(f"/registrations/{registration_id}/confirm-payment")

    def reject_registration(self, registration_id: str) -> Dict[str, Any]:
        """Tolak/batalkan registrasi (admin only)."""
        return self._post(f"/registrations/{registration_id}/cancel")

    def cancel_registration(self, registration_id: str) -> Dict[str, Any]:
        """Batalkan registrasi (user membatalkan tiket sendiri)."""
        return self._post(f"/registrations/{registration_id}/cancel")

    # ── Health ────────────────────────────────────────────

    @staticmethod
    def health_check() -> bool:
        """Cek apakah backend aktif. Kembalikan True jika online."""
        try:
            resp = requests.get("http://localhost:8000/health", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False
