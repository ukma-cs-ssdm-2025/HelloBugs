import pytest
from unittest.mock import MagicMock, patch
from src.api.models.user_model import UserRole


@pytest.fixture
def mock_review():
    """Фікстура для мокування відгуку"""
    return {
        'review_id': 1,
        'user_id': 1,
        'rating': 5,
        'comment': 'Great hotel!',
        'status': 'APPROVED',
        'created_at': '2024-01-01T10:00:00'
    }


@pytest.fixture
def mock_user_guest():
    """Фікстура для звичайного користувача"""
    user = MagicMock()
    user.user_id = 1
    user.email = "user@example.com"
    user.role = UserRole.GUEST
    user.is_admin = False
    return user


@pytest.fixture
def mock_user_admin():
    """Фікстура для адміністратора"""
    user = MagicMock()
    user.user_id = 2
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.is_admin = True
    return user


def test_get_all_reviews_success(client, monkeypatch):
    """Тест GET /api/v1/reviews/ - успішне отримання всіх відгуків"""
    import src.api.routes.reviews as review_routes_module
    
    mock_reviews = [
        {'review_id': 1, 'rating': 5, 'comment': 'Great!'},
        {'review_id': 2, 'rating': 4, 'comment': 'Good'}
    ]
    
    def mock_get_all_reviews(db):
        return mock_reviews
    
    monkeypatch.setattr(review_routes_module, "get_all_reviews", mock_get_all_reviews)
    
    resp = client.get("/api/v1/reviews/")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_user_reviews_success(client, monkeypatch):
    """Тест GET /api/v1/reviews/user/<user_id> - успішне отримання"""
    import src.api.routes.reviews as review_routes_module
    
    mock_reviews = [
        {'review_id': 1, 'user_id': 1, 'rating': 5}
    ]
    
    def mock_get_user_reviews(db, user_id):
        assert user_id == 1
        return mock_reviews
    
    monkeypatch.setattr(review_routes_module, "get_user_reviews", mock_get_user_reviews)
    
    resp = client.get("/api/v1/reviews/user/1")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1

def test_get_average_rating_success(client, monkeypatch):
    """Тест GET /api/v1/reviews/average-rating - успішне отримання"""
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_average_rating(db):
        return 4.5
    
    monkeypatch.setattr(review_routes_module, "get_average_rating", mock_get_average_rating)
    
    resp = client.get("/api/v1/reviews/average-rating")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['average_rating'] == 4.5


def test_get_average_rating_no_reviews(client, monkeypatch):
    """Тест GET /api/v1/reviews/average-rating - немає відгуків"""
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_average_rating(db):
        return 0
    
    monkeypatch.setattr(review_routes_module, "get_average_rating", mock_get_average_rating)
    
    resp = client.get("/api/v1/reviews/average-rating")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data['average_rating'] == 0

def test_get_review_by_id_not_found(client, monkeypatch):
    """Тест GET /api/v1/reviews/<review_id> - відгук не знайдено"""
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return None
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.get("/api/v1/reviews/999")
    assert resp.status_code == 404


def test_patch_review_unauthorized(client):
    """Тест PATCH /api/v1/reviews/<review_id> - без авторизації"""
    resp = client.patch("/api/v1/reviews/1", json={"rating": 4})
    assert resp.status_code == 401


def test_patch_review_not_found(client, monkeypatch, mock_user_guest):
    """Тест PATCH /api/v1/reviews/<review_id> - відгук не знайдено"""
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_guest
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_guest))
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return None
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.patch("/api/v1/reviews/999", 
                        json={"rating": 4},
                        headers={"Authorization": "Bearer token"})
    assert resp.status_code == 404


def test_patch_review_forbidden_not_owner(client, monkeypatch, mock_user_guest, mock_review):
    """Тест PATCH /api/v1/reviews/<review_id> - не власник відгуку (403)"""
    # Користувач з user_id=1 намагається редагувати відгук з user_id=2
    mock_user_guest.user_id = 2
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 2, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_guest
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_guest))
    
    import src.api.routes.reviews as review_routes_module
    
    review_of_another_user = mock_review.copy()
    review_of_another_user['user_id'] = 1  # Відгук належить user_id=1
    
    def mock_get_review_by_id(db, review_id):
        return review_of_another_user
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.patch("/api/v1/reviews/1", 
                        json={"rating": 4},
                        headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403



def test_delete_review_unauthorized(client):
    """Тест DELETE /api/v1/reviews/<review_id> - без авторизації"""
    resp = client.delete("/api/v1/reviews/1")
    assert resp.status_code == 401


def test_delete_review_not_found(client, monkeypatch, mock_user_guest):
    """Тест DELETE /api/v1/reviews/<review_id> - відгук не знайдено"""
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_guest
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_guest))
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return None
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.delete("/api/v1/reviews/999", 
                         headers={"Authorization": "Bearer token"})
    assert resp.status_code == 404


def test_delete_review_forbidden_not_owner(client, monkeypatch, mock_user_guest, mock_review):
    """Тест DELETE /api/v1/reviews/<review_id> - не власник відгуку (403)"""
    mock_user_guest.user_id = 2
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 2, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_guest
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_guest))
    
    import src.api.routes.reviews as review_routes_module
    
    review_of_another_user = mock_review.copy()
    review_of_another_user['user_id'] = 1
    
    def mock_get_review_by_id(db, review_id):
        return review_of_another_user
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.delete("/api/v1/reviews/1", 
                         headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403


def test_delete_review_success_owner(client, monkeypatch, mock_user_guest, mock_review):
    """Тест DELETE /api/v1/reviews/<review_id> - успішне видалення власником"""
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_guest
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_guest))
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return mock_review
    
    def mock_delete_review(db, review_id):
        return True
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    monkeypatch.setattr(review_routes_module, "delete_review", mock_delete_review)
    
    resp = client.delete("/api/v1/reviews/1", 
                         headers={"Authorization": "Bearer token"})
    assert resp.status_code == 204


def test_delete_review_success_admin(client, monkeypatch, mock_user_admin, mock_review):
    """Тест DELETE /api/v1/reviews/<review_id> - успішне видалення адміном"""
    mock_user_admin.role = 'ADMIN'
    
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 2, "role": "ADMIN", "is_admin": True}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_admin
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_admin))
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return mock_review
    
    def mock_delete_review(db, review_id):
        return True
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    monkeypatch.setattr(review_routes_module, "delete_review", mock_delete_review)
    
    resp = client.delete("/api/v1/reviews/1", 
                         headers={"Authorization": "Bearer admin_token"})
    assert resp.status_code == 204


def test_delete_review_value_error(client, monkeypatch, mock_user_guest, mock_review):
    """Тест DELETE /api/v1/reviews/<review_id> - помилка при видаленні (400)"""
    def mock_jwt_decode(token, secret, algorithms=None):
        return {"user_id": 1, "role": "GUEST", "is_admin": False}
    
    mock_query = MagicMock()
    mock_query.get.return_value = mock_user_guest
    
    import src.api.auth as auth_module
    monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
    monkeypatch.setattr("flask.g", MagicMock(current_user=mock_user_guest))
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return mock_review
    
    def mock_delete_review(db, review_id):
        raise ValueError("Cannot delete approved review")
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    monkeypatch.setattr(review_routes_module, "delete_review", mock_delete_review)
    
    resp = client.delete("/api/v1/reviews/1", 
                         headers={"Authorization": "Bearer token"})
    assert resp.status_code == 400


def test_get_all_reviews_empty_list(client, monkeypatch):
    """Тест GET /api/v1/reviews/ - порожній список"""
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_all_reviews(db):
        return []
    
    monkeypatch.setattr(review_routes_module, "get_all_reviews", mock_get_all_reviews)
    
    resp = client.get("/api/v1/reviews/")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data == []


def test_get_user_reviews_empty_list(client, monkeypatch):
    """Тест GET /api/v1/reviews/user/<user_id> - користувач без відгуків"""
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_user_reviews(db, user_id):
        return []
    
    monkeypatch.setattr(review_routes_module, "get_user_reviews", mock_get_user_reviews)
    
    resp = client.get("/api/v1/reviews/user/999")
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data == []
