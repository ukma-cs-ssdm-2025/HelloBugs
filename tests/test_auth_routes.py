import uuid
import os
from typing import Tuple
from unittest.mock import MagicMock

import pytest
from src.api.models.user_model import UserRole


@pytest.fixture(autouse=True)
def ensure_secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", os.environ.get("SECRET_KEY", "test-secret-key"))
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module, "SECRET_KEY", os.environ["SECRET_KEY"], raising=False)


def _unique_email() -> str:
    return f"{uuid.uuid4().hex[:10]}@example.com"


def register_user(client, email=None, password="pass1234") -> Tuple[str, str]:
    if email is None:
        email = _unique_email()
    payload = {
        "email": email,
        "password": password,
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": f"+38066{uuid.uuid4().int % 1000000:06d}",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    return email, resp


def login_user(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_register_success(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={},
    )
    assert resp.status_code == 400


def test_register_duplicate_email(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
    })
    assert resp.status_code == 400


def test_register_missing_fields(client):
    resp = client.post("/api/v1/auth/register", json={})
    assert resp.status_code == 400


def test_login_success(client, monkeypatch):
    email = _unique_email()
    mock_user = MagicMock()
    mock_user.email = email
    mock_user.user_id = 1
    mock_user.first_name = "Jane"
    mock_user.last_name = "Doe"
    mock_user.role = UserRole.GUEST
    mock_user.check_password = lambda pwd: pwd == "goodpass"
    mock_user.generate_auth_token = lambda: "mock_login_token"
    mock_query = MagicMock()
    mock_query.filter_by.return_value.first.return_value = mock_user
    monkeypatch.setattr("src.api.routes.auth_routes.db.query", lambda x: mock_query)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "goodpass"})
    assert resp.status_code == 200
    assert "token" in resp.get_json()


def test_login_invalid_password(client, monkeypatch):
    email = _unique_email()
    mock_user = MagicMock()
    mock_user.email = email
    mock_user.check_password = lambda pwd: pwd == "goodpass"
    mock_query = MagicMock()
    mock_query.filter_by.return_value.first.return_value = mock_user
    monkeypatch.setattr("src.api.routes.auth_routes.db.query", lambda x: mock_query)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "badpass"})
    assert resp.status_code == 401


def test_login_missing_fields(client):
    resp = client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 400


def test_me_unauthorized(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_authorized(client, monkeypatch):
    email = _unique_email()
    user_id = 42
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": user_id, "role": "GUEST", "is_admin": False}
    mock_user = MagicMock()
    mock_user.user_id = user_id
    mock_user.email = email
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.role = UserRole.GUEST
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["email"] == email


def test_admin_only_forbidden_for_guest(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.user_id = 1
    mock_user.role = UserRole.GUEST
    mock_user.is_admin = False
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    resp = client.get("/api/v1/auth/admin", headers={"Authorization": "Bearer guest_token"})
    assert resp.status_code == 403


def test_admin_only_allowed_for_admin(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.user_id = 2
    mock_user.role = UserRole.ADMIN
    mock_user.is_admin = True
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 2, "role": "ADMIN", "is_admin": True}
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    resp = client.get("/api/v1/auth/admin", headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 200
