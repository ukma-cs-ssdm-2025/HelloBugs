import pytest
from unittest.mock import MagicMock, patch
from src.api.models.user_model import UserRole


@pytest.fixture
def mock_contact():
    """Фікстура для мокування контактної інформації"""
    contact = MagicMock()
    contact.id = 1
    contact.hotel_name = "Grand Hotel"
    contact.address = "123 Main Street"
    contact.phone = "+380441234567"
    contact.email = "info@grandhotel.com"
    contact.schedule = "24/7"
    contact.description = "Luxury hotel in the city center"
    return contact


def test_get_contact_info_success(client, monkeypatch, mock_contact):
    """Тест GET /api/v1/contacts/ - успішне отримання контактної інформації"""
    import src.api.routes.contacts as contact_routes_module
    
    def mock_get_contact_info(db):
        return mock_contact
    
    monkeypatch.setattr(contact_routes_module, "get_contact_info", mock_get_contact_info)
    
    resp = client.get("/api/v1/contacts/")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['id'] == 1
    assert data['hotel_name'] == "Grand Hotel"
    assert data['address'] == "123 Main Street"
    assert data['phone'] == "+380441234567"
    assert data['email'] == "info@grandhotel.com"
    assert data['schedule'] == "24/7"
    assert data['description'] == "Luxury hotel in the city center"


def test_get_contact_info_exception(client, monkeypatch):
    import src.api.routes.contacts as contact_routes_module
    
    def mock_get_contact_info(db):
        raise Exception("Database connection failed")
    
    monkeypatch.setattr(contact_routes_module, "get_contact_info", mock_get_contact_info)
    
    resp = client.get("/api/v1/contacts/")
    assert resp.status_code == 500
    
    data = resp.get_json()
    assert "Database connection failed" in data['message']


def test_put_contact_info_unauthorized(client):
    """Тест PUT /api/v1/contacts/ - без авторизації"""
    resp = client.put("/api/v1/contacts/", json={
        "hotel_name": "Updated Hotel"
    })
    assert resp.status_code == 401


def test_put_contact_info_forbidden_non_admin(client, monkeypatch):
    """Тест PUT /api/v1/contacts/ - не адміністратор (403)"""
    mock_user = MagicMock()
    mock_user.user_id = 1
    mock_user.is_admin = False
    mock_user.role = UserRole.GUEST
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user))
    
    resp = client.put("/api/v1/contacts/", 
                      json={"hotel_name": "Updated Hotel"},
                      headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403


def test_put_contact_info_success(client, monkeypatch, mock_contact):
    """Тест PUT /api/v1/contacts/ - успішне оновлення (рядки 32-44)"""
    mock_admin = MagicMock()
    mock_admin.user_id = 1
    mock_admin.is_admin = True
    mock_admin.role = UserRole.ADMIN
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    # Оновлюємо mock_contact з новими даними
    updated_contact = MagicMock()
    updated_contact.id = 1
    updated_contact.hotel_name = "Updated Grand Hotel"
    updated_contact.address = "456 New Street"
    updated_contact.phone = "+380449876543"
    updated_contact.email = "new@grandhotel.com"
    updated_contact.schedule = "Mon-Sun 9:00-22:00"
    updated_contact.description = "Updated description"
    
    import src.api.routes.contacts as contact_routes_module
    
    def mock_update_contact_info(db, data):
        return updated_contact
    
    monkeypatch.setattr(contact_routes_module, "update_contact_info", mock_update_contact_info)
    
    update_data = {
        "hotel_name": "Updated Grand Hotel",
        "address": "456 New Street",
        "phone": "+380449876543",
        "email": "new@grandhotel.com",
        "schedule": "Mon-Sun 9:00-22:00",
        "description": "Updated description"
    }
    
    resp = client.put("/api/v1/contacts/", 
                      json=update_data,
                      headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['id'] == 1
    assert data['hotel_name'] == "Updated Grand Hotel"
    assert data['address'] == "456 New Street"
    assert data['phone'] == "+380449876543"
    assert data['email'] == "new@grandhotel.com"
    assert data['schedule'] == "Mon-Sun 9:00-22:00"
    assert data['description'] == "Updated description"


def test_put_contact_info_exception(client, monkeypatch):
    """Тест PUT /api/v1/contacts/ - обробка винятку (рядок 45)"""
    mock_admin = MagicMock()
    mock_admin.user_id = 1
    mock_admin.is_admin = True
    mock_admin.role = UserRole.ADMIN
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.contacts as contact_routes_module
    
    def mock_update_contact_info(db, data):
        raise Exception("Database update failed")
    
    monkeypatch.setattr(contact_routes_module, "update_contact_info", mock_update_contact_info)
    
    resp = client.put("/api/v1/contacts/", 
                      json={"hotel_name": "Updated Hotel"},
                      headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 500
    
    data = resp.get_json()
    assert "Database update failed" in data['message']


def test_put_contact_info_partial_update(client, monkeypatch, mock_contact):
    """Тест PUT /api/v1/contacts/ - часткове оновлення"""
    mock_admin = MagicMock()
    mock_admin.user_id = 1
    mock_admin.is_admin = True
    mock_admin.role = UserRole.ADMIN
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.contacts as contact_routes_module
    
    # Оновлюємо тільки одне поле
    mock_contact.phone = "+380999999999"
    
    def mock_update_contact_info(db, data):
        return mock_contact
    
    monkeypatch.setattr(contact_routes_module, "update_contact_info", mock_update_contact_info)
    
    resp = client.put("/api/v1/contacts/", 
                      json={"phone": "+380999999999"},
                      headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['phone'] == "+380999999999"


def test_put_contact_info_empty_data(client, monkeypatch, mock_contact):
    """Тест PUT /api/v1/contacts/ - порожні дані"""
    mock_admin = MagicMock()
    mock_admin.user_id = 1
    mock_admin.is_admin = True
    mock_admin.role = UserRole.ADMIN
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    import src.api.routes.contacts as contact_routes_module
    
    def mock_update_contact_info(db, data):
        return mock_contact
    
    monkeypatch.setattr(contact_routes_module, "update_contact_info", mock_update_contact_info)
    
    resp = client.put("/api/v1/contacts/", 
                      json={},
                      headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 200


def test_get_contact_info_public_access(client, monkeypatch, mock_contact):
    """Тест GET /api/v1/contacts/ - публічний доступ без авторизації"""
    import src.api.routes.contacts as contact_routes_module
    
    def mock_get_contact_info(db):
        return mock_contact
    
    monkeypatch.setattr(contact_routes_module, "get_contact_info", mock_get_contact_info)
    
    # Запит без токену - повинен працювати
    resp = client.get("/api/v1/contacts/")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert 'hotel_name' in data
    assert 'address' in data
    assert 'phone' in data


def test_put_contact_info_staff_forbidden(client, monkeypatch):
    """Тест PUT /api/v1/contacts/ - персонал не має доступу (тільки адмін)"""
    mock_staff = MagicMock()
    mock_staff.user_id = 2
    mock_staff.is_admin = False
    mock_staff.role = UserRole.STAFF
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 2, "role": "STAFF", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_staff
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_staff))
    
    resp = client.put("/api/v1/contacts/", 
                      json={"hotel_name": "Updated Hotel"},
                      headers={"Authorization": "Bearer staff_token"})
    assert resp.status_code == 403


def test_put_contact_info_invalid_json(client, monkeypatch):
    """Тест PUT /api/v1/contacts/ - невалідний JSON"""
    mock_admin = MagicMock()
    mock_admin.user_id = 1
    mock_admin.is_admin = True
    mock_admin.role = UserRole.ADMIN
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    # Відправляємо невалідний JSON
    resp = client.put("/api/v1/contacts/",
                      data="invalid json",
                      content_type="application/json",
                      headers={"Authorization": "Bearer admin_token"})
    # Залежно від реалізації може бути 400 або 500
    assert resp.status_code in [400, 500]


def test_get_contact_info_with_none_values(client, monkeypatch):
    """Тест GET /api/v1/contacts/ - коли деякі поля None"""
    mock_contact_none = MagicMock()
    mock_contact_none.id = 1
    mock_contact_none.hotel_name = "Hotel"
    mock_contact_none.address = None
    mock_contact_none.phone = "+380441234567"
    mock_contact_none.email = None
    mock_contact_none.schedule = "24/7"
    mock_contact_none.description = None
    
    import src.api.routes.contacts as contact_routes_module
    
    def mock_get_contact_info(db):
        return mock_contact_none
    
    monkeypatch.setattr(contact_routes_module, "get_contact_info", mock_get_contact_info)
    
    resp = client.get("/api/v1/contacts/")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['id'] == 1
    assert data['hotel_name'] == "Hotel"
    assert data['address'] is None
    assert data['email'] is None
    assert data['description'] is None


def test_put_contact_info_all_fields(client, monkeypatch):
    """Тест PUT /api/v1/contacts/ - оновлення всіх полів одночасно"""
    mock_admin = MagicMock()
    mock_admin.user_id = 1
    mock_admin.is_admin = True
    mock_admin.role = UserRole.ADMIN
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_admin))
    
    updated_contact = MagicMock()
    updated_contact.id = 1
    updated_contact.hotel_name = "New Hotel"
    updated_contact.address = "New Address"
    updated_contact.phone = "+380501111111"
    updated_contact.email = "new@hotel.com"
    updated_contact.schedule = "24/7"
    updated_contact.description = "New description"
    
    import src.api.routes.contacts as contact_routes_module
    
    def mock_update_contact_info(db, data):
        assert 'hotel_name' in data
        assert 'address' in data
        assert 'phone' in data
        assert 'email' in data
        assert 'schedule' in data
        assert 'description' in data
        return updated_contact
    
    monkeypatch.setattr(contact_routes_module, "update_contact_info", mock_update_contact_info)
    
    full_update = {
        "hotel_name": "New Hotel",
        "address": "New Address",
        "phone": "+380501111111",
        "email": "new@hotel.com",
        "schedule": "24/7",
        "description": "New description"
    }
    
    resp = client.put("/api/v1/contacts/", 
                      json=full_update,
                      headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['hotel_name'] == "New Hotel"
    assert data['address'] == "New Address"
    assert data['phone'] == "+380501111111"
    assert data['email'] == "new@hotel.com"
    assert data['schedule'] == "24/7"
    assert data['description'] == "New description"