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


def test_register_no_payload(client):
    resp = client.post("/api/v1/auth/register")
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
    mock_user.generate_auth_token_for_user = lambda: "mock_login_token"
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
    mock_user.phone = "+380661234567"  
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["email"] == email


def test_me_authorized_role_as_string(client, monkeypatch):
    email = _unique_email()
    user_id = 43
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": user_id, "role": "GUEST", "is_admin": False}
    mock_user = MagicMock()
    mock_user.user_id = user_id
    mock_user.email = email
    mock_user.first_name = "Role"
    mock_user.last_name = "String"
    mock_user.role = "GUEST"
    mock_user.phone = "+380661234567"  
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "GUEST"
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


# TDD [RED]: tests for /api/v1/auth/refresh
def test_refresh_unauthorized(client):
    resp = client.get("/api/v1/auth/refresh")
    assert resp.status_code == 401


def test_refresh_success(client, monkeypatch):
    user_id = 777
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": user_id, "role": "GUEST", "is_admin": False}

    mock_user = MagicMock()
    mock_user.user_id = user_id
    mock_user.role = UserRole.GUEST
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user

    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "create_token", lambda user_id, role=None, is_admin=False: "new_token")
    resp = client.get("/api/v1/auth/refresh", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("token") == "new_token"


# TDD cycle2 [RED]: token_type in /api/v1/auth/refresh response
def test_refresh_has_token_type(client, monkeypatch):
    user_id = 888
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": user_id, "role": "GUEST", "is_admin": False}

    mock_user = MagicMock()
    mock_user.user_id = user_id
    mock_user.role = UserRole.GUEST
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user

    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "create_token", lambda user_id, role=None, is_admin=False: "new_token")
    resp = client.get("/api/v1/auth/refresh", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("token_type") == "Bearer"


# TDD cycle3 [RED]: expires_in in /api/v1/auth/refresh response
def test_refresh_has_expires_in(client, monkeypatch):
    user_id = 999
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": user_id, "role": "GUEST", "is_admin": False}

    mock_user = MagicMock()
    mock_user.user_id = user_id
    mock_user.role = UserRole.GUEST
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user

    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "create_token", lambda user_id, role=None, is_admin=False: "new_token")
    resp = client.get("/api/v1/auth/refresh", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("expires_in") == 3600


# TDD [RED]: role echoed back for client convenience
def test_refresh_echoes_role(client, monkeypatch):
    user_id = 1001
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": user_id, "role": "STAFF", "is_admin": False}

    mock_user = MagicMock()
    mock_user.user_id = user_id
    mock_user.role = UserRole.STAFF
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user

    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "create_token", lambda user_id, role=None, is_admin=False: "new_token")
    resp = client.get("/api/v1/auth/refresh", headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("role") == "STAFF"


def test_register_invalid_email_format(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "notanemail",  # без @
        "password": "pass1234",
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 400
    assert "Invalid email format" in resp.get_json()["message"]


def test_register_password_too_short(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "12345",  # менше 6 символів
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 400
    assert "Password must be at least 6 characters" in resp.get_json()["message"]


def test_register_upgrades_guest_user(client, monkeypatch):
    email = _unique_email()
    
    mock_guest = MagicMock()
    mock_guest.user_id = 100
    mock_guest.email = email
    mock_guest.is_registered = False
    mock_guest.role = UserRole.GUEST
    
    mock_upgraded = MagicMock()
    mock_upgraded.user_id = 100
    mock_upgraded.email = email
    mock_upgraded.is_registered = True
    mock_upgraded.to_dict = lambda: {"user_id": 100, "email": email}
    mock_upgraded.generate_auth_token_for_user = lambda: "upgraded_token"
    
    def mock_get_user_by_email(db, email):
        return mock_guest
    
    def mock_update_user_partial(db, user_id, user_data):
        return mock_upgraded
    
    def mock_generate_token(user):
        return "upgraded_token"
    
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(auth_routes_module, "update_user_partial", mock_update_user_partial)
    monkeypatch.setattr(auth_routes_module, "generate_auth_token_for_user", mock_generate_token)
    
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "pass1234",
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 201
    assert "token" in resp.get_json()


def test_register_integrity_error(client, monkeypatch):
    email = _unique_email()
    
    def mock_get_user_by_email(db, email):
        return None
    
    def mock_create_user(db, user_data, via_booking):
        from sqlalchemy.exc import IntegrityError
        raise IntegrityError("duplicate key", None, None)
    
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(auth_routes_module, "create_user", mock_create_user)
    
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "pass1234",
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 409
    assert "already exists" in resp.get_json()["message"]


def test_register_value_error(client, monkeypatch):
    email = _unique_email()
    
    def mock_get_user_by_email(db, email):
        return None
    
    def mock_create_user(db, user_data, via_booking):
        raise ValueError("Invalid data")
    
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(auth_routes_module, "create_user", mock_create_user)
    
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "pass1234",
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 400
    assert "Invalid data" in resp.get_json()["message"]


def test_register_sqlalchemy_error(client, monkeypatch):
    email = _unique_email()
    
    def mock_get_user_by_email(db, email):
        return None
    
    def mock_create_user(db, user_data, via_booking):
        from sqlalchemy.exc import SQLAlchemyError
        raise SQLAlchemyError("Database error")
    
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(auth_routes_module, "create_user", mock_create_user)
    
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "pass1234",
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 500
    assert "Database error" in resp.get_json()["message"]


def test_register_unexpected_error(client, monkeypatch):
    email = _unique_email()
    
    def mock_get_user_by_email(db, email):
        return None
    
    def mock_create_user(db, user_data, via_booking):
        raise Exception("Unexpected error")
    
    import src.api.routes.auth_routes as auth_routes_module
    monkeypatch.setattr(auth_routes_module, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(auth_routes_module, "create_user", mock_create_user)
    
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "pass1234",
        "first_name": "Alice",
        "last_name": "Tester",
        "phone": "+380661234567",
    })
    assert resp.status_code == 500
    assert "unexpected error" in resp.get_json()["message"].lower()

def test_create_admin_unauthorized(client):
    resp = client.post("/api/v1/auth/create-admin")
    assert resp.status_code == 401


def test_create_admin_forbidden_non_admin(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_admin = False
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user))
    
    resp = client.post("/api/v1/auth/create-admin", headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403


def test_create_admin_missing_json(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user))
    
    resp = client.post("/api/v1/auth/create-admin", headers={"Authorization": "Bearer token"})
    assert resp.status_code == 400


def test_create_admin_missing_fields(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user))
    
    resp = client.post("/api/v1/auth/create-admin", 
                      json={"email": "admin@example.com"},
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 400


def test_create_admin_email_exists(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_existing_user = MagicMock()
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    mock_query.filter_by.return_value.first.return_value = mock_existing_user
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.auth_routes as auth_routes_module
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_existing_user
    monkeypatch.setattr(auth_routes_module, "db", mock_db)
    
    resp = client.post("/api/v1/auth/create-admin", 
                      json={
                          "email": "existing@example.com",
                          "password": "pass1234",
                          "first_name": "Admin",
                          "last_name": "User",
                          "phone": "+380661234567"
                      },
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 400


def test_create_admin_success(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    mock_query.filter_by.return_value.first.return_value = None
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.auth_routes as auth_routes_module
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(auth_routes_module, "db", mock_db)
    
    resp = client.post("/api/v1/auth/create-admin", 
                      json={
                          "email": "newadmin@example.com",
                          "password": "pass1234",
                          "first_name": "New",
                          "last_name": "Admin",
                          "phone": "+380661234567"
                      },
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 201


def test_create_admin_database_error(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.auth_routes as auth_routes_module
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    mock_db.add.side_effect = Exception("Database error")
    monkeypatch.setattr(auth_routes_module, "db", mock_db)
    
    resp = client.post("/api/v1/auth/create-admin", 
                      json={
                          "email": "newadmin@example.com",
                          "password": "pass1234",
                          "first_name": "New",
                          "last_name": "Admin",
                          "phone": "+380661234567"
                      },
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 500


def test_create_staff_unauthorized(client):
    resp = client.post("/api/v1/auth/create-staff")
    assert resp.status_code == 401


def test_create_staff_forbidden_non_admin(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_admin = False
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user))
    
    resp = client.post("/api/v1/auth/create-staff", 
                      json={},
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403


def test_create_staff_missing_fields(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    resp = client.post("/api/v1/auth/create-staff", 
                      json={"email": "staff@example.com"},
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 400


def test_create_staff_email_exists(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_existing_user = MagicMock()
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.auth_routes as auth_routes_module
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_existing_user
    monkeypatch.setattr(auth_routes_module, "db", mock_db)
    
    resp = client.post("/api/v1/auth/create-staff", 
                      json={
                          "email": "existing@example.com",
                          "password": "pass1234",
                          "first_name": "Staff",
                          "last_name": "User",
                          "phone": "+380661234567"
                      },
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 400


def test_create_staff_success(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.auth_routes as auth_routes_module
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(auth_routes_module, "db", mock_db)
    
    resp = client.post("/api/v1/auth/create-staff", 
                      json={
                          "email": "newstaff@example.com",
                          "password": "pass1234",
                          "first_name": "New",
                          "last_name": "Staff",
                          "phone": "+380661234567"
                      },
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 201


def test_create_staff_database_error(client, monkeypatch):
    mock_admin = MagicMock()
    mock_admin.is_admin = True
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.auth_routes as auth_routes_module
    mock_db = MagicMock()
    mock_db.query.return_value.filter_by.return_value.first.return_value = None
    mock_db.add.side_effect = Exception("Database error")
    monkeypatch.setattr(auth_routes_module, "db", mock_db)
    
    resp = client.post("/api/v1/auth/create-staff", 
                      json={
                          "email": "newstaff@example.com",
                          "password": "pass1234",
                          "first_name": "New",
                          "last_name": "Staff",
                          "phone": "+380661234567"
                      },
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 500
