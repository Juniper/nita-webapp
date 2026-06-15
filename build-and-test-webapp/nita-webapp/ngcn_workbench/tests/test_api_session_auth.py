# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the session auth endpoints:
GET  /api/v1/auth/csrf/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
GET  /api/v1/auth/me/
"""

import pytest
from rest_framework.test import APIClient

# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── GET /api/v1/auth/csrf/ ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_csrf_endpoint_returns_token(api_client):
    """CSRF endpoint is public and returns a non-empty token."""
    response = api_client.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    data = response.json()
    assert "csrfToken" in data
    assert isinstance(data["csrfToken"], str)
    assert len(data["csrfToken"]) > 0


# ── POST /api/v1/auth/login/ ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_login_valid_credentials_returns_user(user, api_client):
    """Valid credentials return 200 with user info."""
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "tester", "password": "secret"},
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "tester"
    assert data["id"] == user.pk
    assert "is_superuser" in data


@pytest.mark.django_db
def test_login_invalid_credentials_returns_400(api_client):
    """Wrong password returns 400 with a detail field."""
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": "nobody", "password": "wrongpass"},
        format="json",
    )
    assert response.status_code == 400
    assert "detail" in response.json()


# ── POST /api/v1/auth/logout/ ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_logout_authenticated_returns_204(auth_api_client):
    """Authenticated logout returns 204 No Content."""
    response = auth_api_client.post("/api/v1/auth/logout/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_logout_unauthenticated_returns_403(api_client):
    """Unauthenticated logout is rejected."""
    response = api_client.post("/api/v1/auth/logout/")
    assert response.status_code in (401, 403)


# ── GET /api/v1/auth/me/ ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_me_authenticated_returns_user(user, auth_api_client):
    """Authenticated me endpoint returns id, username, is_superuser."""
    response = auth_api_client.get("/api/v1/auth/me/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.pk
    assert data["username"] == "tester"
    assert "is_superuser" in data


@pytest.mark.django_db
def test_me_unauthenticated_returns_403(api_client):
    """Unauthenticated me request is rejected."""
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code in (401, 403)
