"""
Test Events Endpoints
=====================
Unit test untuk endpoint /api/v1/events/*
"""

import pytest
from unittest.mock import patch


# ── List Events ───────────────────────────────────────────

class TestListEvents:

    def test_list_events_default(self, client, dummy_event):
        """GET /events tanpa filter harus return list event."""
        with patch("backend.services.EventService.search_events") as mock_search:
            mock_search.return_value = [dummy_event]
            resp = client.get("/api/v1/events/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert data["count"] >= 0

    def test_list_events_with_filter(self, client, dummy_event):
        """GET /events dengan query filter harus melewatkan parameter ke service."""
        with patch("backend.services.EventService.search_events") as mock_search:
            mock_search.return_value = [dummy_event]
            resp = client.get("/api/v1/events/?q=tech&location=Jakarta&status=upcoming")
        assert resp.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["query"] == "tech"
        assert call_kwargs["location"] == "Jakarta"

    def test_list_events_pagination(self, client):
        """Pagination page/page_size harus diteruskan dengan benar."""
        with patch("backend.services.EventService.search_events") as mock_search:
            mock_search.return_value = []
            resp = client.get("/api/v1/events/?page=2&page_size=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 5


# ── Get Event Detail ──────────────────────────────────────

class TestGetEvent:

    def test_get_event_found(self, client, dummy_event):
        """GET /events/{id} untuk event yang ada harus return detail."""
        with patch("backend.services.EventService.get_event_detail") as mock_get:
            mock_get.return_value = dummy_event
            resp = client.get("/api/v1/events/event-uuid-001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Tech Conference 2026"

    def test_get_event_not_found(self, client):
        """GET /events/{id} untuk event yang tidak ada harus return 404."""
        with patch("backend.services.EventService.get_event_detail") as mock_get:
            mock_get.return_value = None
            resp = client.get("/api/v1/events/not-exist-id")
        assert resp.status_code == 404


# ── Trending & Upcoming ───────────────────────────────────

class TestSpecialLists:

    def test_trending_events(self, client, dummy_event):
        with patch("backend.services.RecommendationService.get_trending_events") as mock:
            mock.return_value = [dummy_event]
            resp = client.get("/api/v1/events/trending")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_upcoming_events(self, client, dummy_event):
        with patch("backend.services.RecommendationService.get_upcoming_events") as mock:
            mock.return_value = [dummy_event]
            resp = client.get("/api/v1/events/upcoming")
        assert resp.status_code == 200


# ── Create Event ──────────────────────────────────────────

class TestCreateEvent:

    def test_create_event_as_organizer(self, client, dummy_event, mock_decode_token_organizer):
        """Organizer harus bisa membuat event baru."""
        with patch("backend.repositories.UserRepository.get_by_id") as mock_user, \
             patch("backend.services.EventService.create_event") as mock_create:
            mock_user.return_value = {"id": "organizer-uuid-001", "role": "organizer"}
            mock_create.return_value = {"success": True, "event": dummy_event}

            resp = client.post(
                "/api/v1/events/",
                json={
                    "title": "Tech Conference 2026",
                    "description": "Konferensi teknologi terbesar",
                    "short_description": "Tech event 2026",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-02",
                    "location": "Jakarta",
                },
                headers={"Authorization": "Bearer organizer-token"},
            )
        assert resp.status_code == 201
        assert resp.json()["success"] is True

    def test_create_event_as_participant_forbidden(self, client, mock_decode_token):
        """Participant tidak boleh membuat event."""
        with patch("backend.repositories.UserRepository.get_by_id") as mock_user:
            mock_user.return_value = {"id": "user-uuid-001", "role": "participant"}
            resp = client.post(
                "/api/v1/events/",
                json={
                    "title": "Test Event Participant",
                    "description": "Deskripsi event test",
                    "short_description": "Short desc",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-02",
                    "location": "Jakarta",
                },
                headers={"Authorization": "Bearer participant-token"},
            )
        assert resp.status_code == 403

    def test_create_event_no_auth(self, client):
        """Tanpa token harus return 401."""
        resp = client.post("/api/v1/events/", json={
            "title": "Test Event No Auth",
            "description": "Deskripsi event test tanpa auth",
            "short_description": "Short desc",
            "start_date": "2026-08-01",
            "end_date": "2026-08-02",
            "location": "Jakarta",
        })
        assert resp.status_code == 401


# ── Recommendations ───────────────────────────────────────

class TestRecommendations:

    def test_event_recommendations(self, client, dummy_event):
        with patch("backend.services.RecommendationService.get_similar_events") as mock:
            mock.return_value = [dummy_event]
            resp = client.get("/api/v1/events/event-uuid-001/recommendations")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
