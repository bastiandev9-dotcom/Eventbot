"""
Test Configuration & Fixtures
==============================
Shared fixtures untuk semua test module EventBot.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from typing import Dict


# ── App client ────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient — pakai mock DB supaya tidak butuh koneksi nyata.
    """
    with patch("backend.config.database.get_connection_pool", return_value=MagicMock()):
        from backend.main import app
        yield TestClient(app)


# ── Dummy data ────────────────────────────────────────────

@pytest.fixture
def dummy_user() -> Dict:
    return {
        "id": "user-uuid-001",
        "name": "Budi Santoso",
        "email": "budi@test.com",
        "role": "participant",
        "phone": "08123456789",
        "password_hash": "$2b$12$hashedpassword",
    }


@pytest.fixture
def dummy_organizer() -> Dict:
    return {
        "id": "organizer-uuid-001",
        "name": "Organizer Corp",
        "email": "org@test.com",
        "role": "organizer",
    }


@pytest.fixture
def dummy_event() -> Dict:
    return {
        "id": "event-uuid-001",
        "title": "Tech Conference 2026",
        "slug": "tech-conference-2026",
        "description": "Konferensi teknologi terbesar",
        "short_description": "Tech event 2026",
        "start_date": "2026-08-01",
        "end_date": "2026-08-02",
        "location": "Jakarta",
        "status": "upcoming",
        "is_published": True,
        "organizer_id": "organizer-uuid-001",
    }


@pytest.fixture
def dummy_ticket() -> Dict:
    return {
        "id": "ticket-uuid-001",
        "event_id": "event-uuid-001",
        "name": "Early Bird",
        "price": 150000,
        "quota": 100,
        "sold": 10,
        "available": True,
        "remaining": 90,
        "max_per_order": 5,
    }


@pytest.fixture
def dummy_registration() -> Dict:
    return {
        "id": "reg-uuid-001",
        "user_id": "user-uuid-001",
        "ticket_id": "ticket-uuid-001",
        "quantity": 2,
        "total_price": 300000,
        "status": "pending",
        "success": True,
        "registration_id": "reg-uuid-001",
        "message": "Booking berhasil",
    }


@pytest.fixture
def auth_header() -> Dict[str, str]:
    """Header Authorization dengan token dummy."""
    return {"Authorization": "Bearer dummy-jwt-token"}


# ── JWT mock helper ───────────────────────────────────────

@pytest.fixture
def mock_decode_token():
    """Mock decode_token supaya selalu return payload valid (participant)."""
    # Patch di tempat decode_token di-import dan dipakai (deps.py)
    with patch("backend.api.deps.decode_token") as mock:
        mock.return_value = {
            "sub": "user-uuid-001",
            "email": "budi@test.com",
            "role": "participant",
        }
        yield mock


@pytest.fixture
def mock_decode_token_organizer():
    """Mock decode_token untuk user organizer."""
    with patch("backend.api.deps.decode_token") as mock:
        mock.return_value = {
            "sub": "organizer-uuid-001",
            "email": "org@test.com",
            "role": "organizer",
        }
        yield mock
