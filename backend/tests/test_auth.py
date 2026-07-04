"""
Test Auth Endpoints
===================
Unit test untuk endpoint /api/v1/auth/*
"""

import pytest
from unittest.mock import patch, MagicMock


# ── Register ──────────────────────────────────────────────

class TestRegister:

    def test_register_success(self, client, dummy_user):
        """Register dengan data valid harus sukses."""
        with patch("backend.services.AuthService.register") as mock_reg:
            mock_reg.return_value = {
                "success": True,
                "message": "Registrasi berhasil",
                "user": dummy_user,
            }
            resp = client.post("/api/v1/auth/register", json={
                "name": "Budi Santoso",
                "email": "budi@test.com",
                "password": "secret123",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert "user" in data

    def test_register_duplicate_email(self, client):
        """Register dengan email yang sudah terdaftar harus gagal."""
        with patch("backend.services.AuthService.register") as mock_reg:
            mock_reg.return_value = {
                "success": False,
                "message": "Email sudah terdaftar",
            }
            resp = client.post("/api/v1/auth/register", json={
                "name": "Duplikat User",
                "email": "budi@test.com",
                "password": "secret123",
            })
        assert resp.status_code == 400
        assert "Email sudah terdaftar" in resp.json()["detail"]

    def test_register_missing_fields(self, client):
        """Register tanpa field wajib harus return 422."""
        resp = client.post("/api/v1/auth/register", json={"name": "Budi"})
        assert resp.status_code == 422

    def test_register_short_password(self, client):
        """Password kurang dari 6 karakter harus ditolak."""
        resp = client.post("/api/v1/auth/register", json={
            "name": "Budi",
            "email": "budi@test.com",
            "password": "123",
        })
        assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────

class TestLogin:

    def test_login_success(self, client, dummy_user):
        """Login dengan kredensial benar harus return token."""
        with patch("backend.services.AuthService.login") as mock_login:
            mock_login.return_value = {
                "success": True,
                "access_token": "jwt.token.here",
                "user": dummy_user,
            }
            resp = client.post("/api/v1/auth/login", json={
                "email": "budi@test.com",
                "password": "secret123",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Login dengan password salah harus return 401."""
        with patch("backend.services.AuthService.login") as mock_login:
            mock_login.return_value = {
                "success": False,
                "message": "Email atau password salah",
            }
            resp = client.post("/api/v1/auth/login", json={
                "email": "budi@test.com",
                "password": "wrongpassword",
            })
        assert resp.status_code == 401

    def test_login_invalid_email(self, client):
        """Login dengan email tidak valid harus return 422."""
        resp = client.post("/api/v1/auth/login", json={
            "email": "bukan-email",
            "password": "secret123",
        })
        assert resp.status_code == 422


# ── Get Profile ───────────────────────────────────────────

class TestGetProfile:

    def test_get_profile_success(self, client, dummy_user, mock_decode_token):
        """GET /me dengan token valid harus return user."""
        with patch("backend.repositories.UserRepository.get_by_id") as mock_get:
            mock_get.return_value = dummy_user
            resp = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer valid-token"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "user" in data
        # password_hash tidak boleh ada di response
        assert "password_hash" not in data.get("user", {})

    def test_get_profile_no_token(self, client):
        """GET /me tanpa token harus return 401."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_profile_invalid_token(self, client):
        """GET /me dengan token tidak valid harus return 401."""
        with patch("backend.api.deps.decode_token", side_effect=Exception("Invalid")):
            resp = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid"},
            )
        assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────

class TestLogout:

    def test_logout(self, client):
        """Logout selalu return 200."""
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
