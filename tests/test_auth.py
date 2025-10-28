import os
import uuid
import pytest
from flask import Flask
from src.api.models.user_model import UserRole
from src.api.auth import token_required, admin_required, staff_required, role_required, validate_password


@pytest.fixture(autouse=True)
def ensure_secret_key(monkeypatch):
   monkeypatch.setenv("SECRET_KEY", os.environ.get("SECRET_KEY", "test-secret-key"))
   import src.api.auth as auth_module
   monkeypatch.setattr(auth_module, "SECRET_KEY", os.environ["SECRET_KEY"], raising=False)


@pytest.fixture
def app():
   app = Flask(__name__)
   return app


@pytest.fixture
def client(app):
   return app.test_client()


def _add_view(app, decorator):
   endpoint = f"ep_{uuid.uuid4().hex[:8]}"


   @decorator
   def _view():
       return ("ok", 200)


   app.add_url_rule(f"/{endpoint}", endpoint, _view, methods=["GET"])
   return f"/{endpoint}"


def test_token_required_no_token(app, client):
   path = _add_view(app, token_required)
   resp = client.get(path)
   assert resp.status_code == 401


def test_token_required_invalid_token(monkeypatch, app, client):
   import jwt as pyjwt
   path = _add_view(app, token_required)


   def _raise_invalid(*args, **kwargs):
       raise pyjwt.InvalidTokenError("bad token")


   monkeypatch.setattr("src.api.auth.jwt.decode", _raise_invalid)
   resp = client.get(path, headers={"Authorization": "Bearer abc"})
   assert resp.status_code == 401


def test_token_required_expired(monkeypatch, app, client):
   import jwt as pyjwt
   path = _add_view(app, token_required)


   def _raise_expired(*args, **kwargs):
       raise pyjwt.ExpiredSignatureError("expired")


   monkeypatch.setattr("src.api.auth.jwt.decode", _raise_expired)
   resp = client.get(path, headers={"Authorization": "Bearer abc"})
   assert resp.status_code == 401


def test_token_required_user_not_found(monkeypatch, app, client):
   path = _add_view(app, token_required)
   def _fake_decode(token, secret, algorithms=None):
       return {"user_id": 999999}


   class _Q:
       def get(self, _):
           return None


   class _DBStub:
       def query(self, _model):
           return _Q()


   monkeypatch.setattr("src.api.auth.jwt.decode", _fake_decode)
   import src.api.auth as auth_module
   monkeypatch.setattr(auth_module, "db", _DBStub())


   resp = client.get(path, headers={"Authorization": "Bearer abc"})
   assert resp.status_code == 401


def test_admin_required_forbidden(app, client):
   class _User:
       def __init__(self):
           self.role = UserRole.GUEST


   def _fake_decode(*args, **kwargs):
       return {"user_id": 999, "is_admin": False}


   class _Q:
       def get(self, _):
           return _User()


   class _DB:
       def query(self, _):
           return _Q()


   import src.api.auth as auth_module
   import src.api.auth as auth
   auth.jwt.decode = _fake_decode
   auth_module.db = _DB()


   def decorated():
       return ("ok", 200)


   view = token_required(admin_required(decorated))
   endpoint = f"/admin_{uuid.uuid4().hex[:6]}"
   app.add_url_rule(endpoint, endpoint.strip("/"), view)


   resp = client.get(endpoint, headers={"Authorization": f"Bearer any"})
   assert resp.status_code == 403


def test_admin_required_allowed(app, client):
   admin_id = 12345


   class _User:
       def __init__(self):
           self.role = UserRole.ADMIN


   def _fake_decode(*args, **kwargs):
       return {"user_id": admin_id, "is_admin": True}


   class _Q:
       def get(self, _):
           return _User()


   class _DB:
       def query(self, _):
           return _Q()


   def decorated():
       return ("ok", 200)


   import src.api.auth as auth_module
   import src.api.auth as auth
   auth.jwt.decode = _fake_decode
   auth_module.db = _DB()


   view = token_required(admin_required(decorated))
   endpoint = f"/admin_{uuid.uuid4().hex[:6]}"
   app.add_url_rule(endpoint, endpoint.strip("/"), view)


   resp = client.get(endpoint, headers={"Authorization": f"Bearer dummy"})
   assert resp.status_code == 200


def test_staff_required_forbidden_for_guest(app, client):
   class _User:
       def __init__(self):
           self.role = UserRole.GUEST


   def _fake_decode(*args, **kwargs):
       return {"user_id": 1, "is_admin": False}


   class _Q:
       def get(self, _):
           return _User()


   class _DB:
       def query(self, _):
           return _Q()


   import src.api.auth as auth_module
   import src.api.auth as auth
   auth.jwt.decode = _fake_decode
   auth_module.db = _DB()


   def decorated():
       return ("ok", 200)


   view = token_required(staff_required(decorated))
   endpoint = f"/staff_{uuid.uuid4().hex[:6]}"
   app.add_url_rule(endpoint, endpoint.strip("/"), view)


   resp = client.get(endpoint, headers={"Authorization": f"Bearer any"})
   assert resp.status_code == 403


def test_staff_required_allowed_for_staff(app, client):
   class _User:
       def __init__(self):
           self.role = UserRole.STAFF


   def _fake_decode(*args, **kwargs):
       return {"user_id": 2, "is_admin": False}


   class _Q:
       def get(self, _):
           return _User()


   class _DB:
       def query(self, _):
           return _Q()


   import src.api.auth as auth_module
   import src.api.auth as auth
   auth.jwt.decode = _fake_decode
   auth_module.db = _DB()


   def decorated():
       return ("ok", 200)


   view = token_required(staff_required(decorated))
   endpoint = f"/staff_{uuid.uuid4().hex[:6]}"
   app.add_url_rule(endpoint, endpoint.strip("/"), view)


   resp = client.get(endpoint, headers={"Authorization": f"Bearer any"})
   assert resp.status_code == 200


def test_role_required_only_staff_allowed(app, client):
   class _User:
       def __init__(self):
           self.role = UserRole.ADMIN


   def _fake_decode(*args, **kwargs):
       return {"user_id": 3, "is_admin": True}


   class _Q:
       def get(self, _):
           return _User()


   class _DB:
       def query(self, _):
           return _Q()


   import src.api.auth as auth_module
   import src.api.auth as auth
   auth.jwt.decode = _fake_decode
   auth_module.db = _DB()


   def decorated():
       return ("ok", 200)


   view = token_required(role_required("STAFF")(decorated))
   endpoint = f"/role_{uuid.uuid4().hex[:6]}"
   app.add_url_rule(endpoint, endpoint.strip("/"), view)


   resp = client.get(endpoint, headers={"Authorization": f"Bearer any"})
   assert resp.status_code == 403


def test_role_required_staff_or_admin_allowed(app, client):
   class _User:
       def __init__(self):
           self.role = UserRole.ADMIN


   def _fake_decode(*args, **kwargs):
       return {"user_id": 4, "is_admin": True}


   class _Q:
       def get(self, _):
           return _User()


   class _DB:
       def query(self, _):
           return _Q()


   import src.api.auth as auth_module
   import src.api.auth as auth
   auth.jwt.decode = _fake_decode
   auth_module.db = _DB()


   def decorated():
       return ("ok", 200)


   view = token_required(role_required("STAFF", "ADMIN")(decorated))
   endpoint = f"/role_{uuid.uuid4().hex[:6]}"
   app.add_url_rule(endpoint, endpoint.strip("/"), view)


   resp = client.get(endpoint, headers={"Authorization": f"Bearer any"})
   assert resp.status_code == 200

# TDD [RED]: is_token_expired helper
def test_is_token_expired_with_expired_token(monkeypatch):
   import jwt as pyjwt
   import src.api.auth as auth
   
   def _raise_expired(*args, **kwargs):
       raise pyjwt.ExpiredSignatureError("expired")
   
   monkeypatch.setattr("src.api.auth.jwt.decode", _raise_expired)
   assert auth.is_token_expired("any_token") is True

def test_is_token_expired_with_valid_token(monkeypatch):
   import src.api.auth as auth
   
   def _valid_decode(token, secret, algorithms=None):
       return {"user_id": 1, "exp": 9999999999}
   
   monkeypatch.setattr("src.api.auth.jwt.decode", _valid_decode)
   assert auth.is_token_expired("valid_token") is False

def test_is_token_expired_with_invalid_token(monkeypatch):
   import jwt as pyjwt
   import src.api.auth as auth
   
   def _raise_invalid(*args, **kwargs):
       raise pyjwt.InvalidTokenError("bad token")
   
   monkeypatch.setattr("src.api.auth.jwt.decode", _raise_invalid)
   assert auth.is_token_expired("bad_token") is True


def test_validate_password():
    is_valid, message = validate_password("PassWord&123!")
    assert is_valid == True
    assert message == "Password is valid"

    is_valid, message = validate_password("short")
    assert is_valid == False
    assert "at least 8 characters" in message

    is_valid, message = validate_password("12092006k")
    assert is_valid == False
    assert "uppercase" in message

    is_valid, message = validate_password(" ")
    assert is_valid == False
    assert "spaces" in message

    is_valid, message = validate_password("")
    assert is_valid == False
    assert "empty" in message

