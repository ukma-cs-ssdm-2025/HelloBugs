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

def test_create_token_bytes_handling(monkeypatch):
    """Тест обробки bytes від PyJWT v1"""
    import src.api.auth as auth
    
    def mock_encode(payload, secret, algorithm):
        return b'test.token.bytes'
    
    monkeypatch.setattr("src.api.auth.jwt.encode", mock_encode)
    
    token = auth.create_token(1, role='GUEST', is_admin=False)
    
    assert isinstance(token, str)
    assert token == 'test.token.bytes'


def test_create_token_string_handling(monkeypatch):
    """Тест обробки string від PyJWT v2"""
    import src.api.auth as auth
    
    def mock_encode(payload, secret, algorithm):
        return 'test.token.string'
    
    monkeypatch.setattr("src.api.auth.jwt.encode", mock_encode)
    
    token = auth.create_token(1, role='GUEST', is_admin=False)
    
    assert isinstance(token, str)
    assert token == 'test.token.string'


def test_verify_auth_token_success(monkeypatch):
    """Тест успішної верифікації токену"""
    import src.api.auth as auth
    from unittest.mock import MagicMock
    
    mock_user = MagicMock()
    mock_user.user_id = 1
    
    def mock_decode(token, secret, algorithms):
        return {'user_id': 1}
    
    class _Q:
        def get(self, user_id):
            return mock_user if user_id == 1 else None
    
    class _DB:
        def query(self, model):
            return _Q()
    
    monkeypatch.setattr("src.api.auth.jwt.decode", mock_decode)
    monkeypatch.setattr(auth, "db", _DB())
    
    result = auth.verify_auth_token("valid_token")
    
    assert result == mock_user


def test_verify_auth_token_invalid_token(monkeypatch):
    """Тест верифікації невалідного токену"""
    import src.api.auth as auth
    import jwt as pyjwt
    
    def mock_decode(token, secret, algorithms):
        raise pyjwt.InvalidTokenError("Invalid token")
    
    monkeypatch.setattr("src.api.auth.jwt.decode", mock_decode)
    
    result = auth.verify_auth_token("invalid_token")
    
    assert result is None


def test_verify_auth_token_user_not_found(monkeypatch):
    """Тест верифікації токену коли користувач не знайдений"""
    import src.api.auth as auth
    
    def mock_decode(token, secret, algorithms):
        return {'user_id': 999}
    
    class _Q:
        def get(self, user_id):
            return None
    
    class _DB:
        def query(self, model):
            return _Q()
    
    monkeypatch.setattr("src.api.auth.jwt.decode", mock_decode)
    monkeypatch.setattr(auth, "db", _DB())
    
    result = auth.verify_auth_token("valid_token")
    
    assert result is None


def test_staff_required_no_current_user(app, client):
    """Тест staff_required коли немає current_user в g"""
    from src.api.auth import staff_required
    from flask import g
    
    def decorated():
        return ("ok", 200)
    
    view = staff_required(decorated)
    endpoint = f"/staff_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    with app.test_request_context():
        if hasattr(g, 'current_user'):
            delattr(g, 'current_user')
        
        resp = client.get(endpoint)
        assert resp.status_code == 401


def test_role_required_no_current_user(app, client):
    """Тест role_required коли немає current_user в g"""
    from src.api.auth import role_required
    from flask import g
    
    def decorated():
        return ("ok", 200)
    
    view = role_required("STAFF")(decorated)
    endpoint = f"/role_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    with app.test_request_context():
        if hasattr(g, 'current_user'):
            delattr(g, 'current_user')
        
        resp = client.get(endpoint)
        assert resp.status_code == 401


def test_login_required_web_with_bearer_token(app, client, monkeypatch):
    """Тест login_required_web з Bearer токеном в header"""
    from src.api.auth import login_required_web
    from src.api.models.user_model import UserRole
    
    class _User:
        def __init__(self):
            self.user_id = 2
            self.role = UserRole.STAFF
    
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": 2, "is_admin": False}
    
    class _Q:
        def get(self, _):
            return _User()
    
    class _DB:
        def query(self, _):
            return _Q()
    
    import src.api.auth as auth_module
    monkeypatch.setattr("src.api.auth.jwt.decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", _DB())
    
    def decorated():
        return ("ok", 200)
    
    view = login_required_web(decorated)
    endpoint = f"/web_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200



def test_login_required_web_invalid_token(app, client, monkeypatch):
    """Тест login_required_web з невалідним токеном"""
    from src.api.auth import login_required_web
    import jwt as pyjwt
    
    def _raise_invalid(token, secret, algorithms=None):
        raise pyjwt.InvalidTokenError("invalid")
    
    monkeypatch.setattr("src.api.auth.jwt.decode", _raise_invalid)
    
    def decorated():
        return ("ok", 200)
    
    view = login_required_web(decorated)
    endpoint = f"/web_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer bad_token"})
    assert resp.status_code == 401


def test_token_optional_no_token(app, client):
    """Тест token_optional без токену - дозволяє доступ"""
    from src.api.auth import token_optional
    
    def decorated():
        return ("ok", 200)
    
    view = token_optional(decorated)
    endpoint = f"/optional_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint)
    assert resp.status_code == 200


def test_token_optional_with_valid_token(app, client, monkeypatch):
    """Тест token_optional з валідним токеном"""
    from src.api.auth import token_optional
    from src.api.models.user_model import UserRole
    from flask import g
    
    class _User:
        def __init__(self):
            self.user_id = 1
            self.role = UserRole.GUEST
    
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": 1, "is_admin": False}
    
    class _Q:
        def get(self, _):
            return _User()
    
    class _DB:
        def query(self, _):
            return _Q()
    
    import src.api.auth as auth_module
    monkeypatch.setattr("src.api.auth.jwt.decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", _DB())
    
    def decorated():
        assert hasattr(g, 'current_user')
        return ("ok", 200)
    
    view = token_optional(decorated)
    endpoint = f"/optional_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200


def test_token_optional_with_expired_token(app, client, monkeypatch):
    """Тест token_optional з протермінованим токеном - ігнорує помилку"""
    from src.api.auth import token_optional
    import jwt as pyjwt
    
    def _raise_expired(token, secret, algorithms=None):
        raise pyjwt.ExpiredSignatureError("expired")
    
    monkeypatch.setattr("src.api.auth.jwt.decode", _raise_expired)
    
    def decorated():
        return ("ok", 200)
    
    view = token_optional(decorated)
    endpoint = f"/optional_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer expired_token"})
    assert resp.status_code == 200


def test_token_optional_with_invalid_token(app, client, monkeypatch):
    """Тест token_optional з невалідним токеном - ігнорує помилку"""
    from src.api.auth import token_optional
    import jwt as pyjwt
    
    def _raise_invalid(token, secret, algorithms=None):
        raise pyjwt.InvalidTokenError("invalid")
    
    monkeypatch.setattr("src.api.auth.jwt.decode", _raise_invalid)
    
    def decorated():
        return ("ok", 200)
    
    view = token_optional(decorated)
    endpoint = f"/optional_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer bad_token"})
    assert resp.status_code == 200


def test_token_optional_user_not_found(app, client, monkeypatch):
    """Тест token_optional коли користувач не знайдений - продовжує без помилки"""
    from src.api.auth import token_optional
    
    def _fake_decode(token, secret, algorithms=None):
        return {"user_id": 999, "is_admin": False}
    
    class _Q:
        def get(self, _):
            return None 
    
    class _DB:
        def query(self, _):
            return _Q()
    
    import src.api.auth as auth_module
    monkeypatch.setattr("src.api.auth.jwt.decode", _fake_decode)
    monkeypatch.setattr(auth_module, "db", _DB())
    
    def decorated():
        return ("ok", 200)
    
    view = token_optional(decorated)
    endpoint = f"/optional_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer valid_token"})
    assert resp.status_code == 200


def test_generate_auth_token_for_user(monkeypatch):
    """Тест генерації токену для користувача"""
    import src.api.auth as auth
    from src.api.models.user_model import UserRole
    from unittest.mock import MagicMock
    
    mock_user = MagicMock()
    mock_user.user_id = 1
    mock_user.role = UserRole.ADMIN
    
    def mock_create_token(user_id, role=None, is_admin=False):
        return f"token_for_{user_id}"
    
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    
    token = auth.generate_auth_token_for_user(mock_user)
    
    assert token == "token_for_1"


def test_generate_auth_token_for_user_no_role(monkeypatch):
    """Тест генерації токену для користувача без ролі"""
    import src.api.auth as auth
    from unittest.mock import MagicMock
    
    mock_user = MagicMock()
    mock_user.user_id = 2
    mock_user.role = None
    
    def mock_create_token(user_id, role=None, is_admin=False):
        assert role == 'GUEST'  # Повинно бути 'GUEST' якщо роль None
        return f"token_for_{user_id}"
    
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    
    token = auth.generate_auth_token_for_user(mock_user)
    
    assert token == "token_for_2"


def test_staff_required_with_role_string(app, client):
    """Тест staff_required коли role є string, а не enum"""
    from src.api.auth import staff_required, token_required
    from unittest.mock import MagicMock
    
    class _User:
        def __init__(self):
            self.role = 'STAFF'  # String замість enum
    
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
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer token"})
    assert resp.status_code == 200


def test_role_required_with_role_string(app, client):
    """Тест role_required коли role є string, а не enum"""
    from src.api.auth import role_required, token_required
    
    class _User:
        def __init__(self):
            self.role = 'ADMIN'  # String замість enum
    
    def _fake_decode(*args, **kwargs):
        return {"user_id": 1, "is_admin": True}
    
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
    
    view = token_required(role_required("ADMIN")(decorated))
    endpoint = f"/role_{uuid.uuid4().hex[:6]}"
    app.add_url_rule(endpoint, endpoint.strip("/"), view)
    
    resp = client.get(endpoint, headers={"Authorization": "Bearer token"})
    assert resp.status_code == 200