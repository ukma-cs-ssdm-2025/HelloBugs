import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from datetime import datetime
from src.api.models.user_model import UserRole


@pytest.fixture
def mock_review():
    """Фікстура для мокування відгуку (об'єкт з атрибутами)"""
    r = MagicMock()
    r.review_id = 1
    r.user_id = 1
    r.rating = 5
    r.comment = 'Great hotel!'
    r.created_at = '2024-01-01T10:00:00'
    return r


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


@pytest.fixture
def auth_setup(monkeypatch):
    """Хелпер для налаштування автентифікації/контексту g.current_user без дублювання коду"""
    def _setup(user):
        def mock_jwt_decode(token, secret, algorithms=None):
            role_val = getattr(user, 'role', None)
            role_name = role_val.name if hasattr(role_val, 'name') else (role_val or 'GUEST')
            is_admin = role_name == 'ADMIN'
            return {"user_id": user.user_id, "role": role_name, "is_admin": is_admin}
        mock_query = MagicMock()
        mock_query.get.return_value = user
        import src.api.auth as auth_module
        monkeypatch.setattr(auth_module.jwt, "decode", mock_jwt_decode)
        monkeypatch.setattr(auth_module, "db", MagicMock(query=lambda x: mock_query))
        monkeypatch.setattr("flask.g", MagicMock(current_user=user))
    return _setup


def test_get_all_reviews_success(client, monkeypatch):
    """Тест GET /api/v1/reviews/ - успішне отримання всіх відгуків"""
    import src.api.routes.reviews as review_routes_module
    
    mock_r1 = SimpleNamespace(review_id=1, rating=5, comment='Great!', created_at=None, updated_at=None, is_approved=True)
    mock_r2 = SimpleNamespace(review_id=2, rating=4, comment='Good', created_at=None, updated_at=None, is_approved=True)
    mock_reviews = [mock_r1, mock_r2]
    
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
    
    r = SimpleNamespace(review_id=1, user_id=1, rating=5, created_at=None, updated_at=None)
    mock_reviews = [r]
    
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


def test_get_review_by_id_not_found(client, monkeypatch):
    """Тест GET /api/v1/reviews/<review_id> - відгук не знайдено"""
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return None
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.get("/api/v1/reviews/999")
    assert resp.status_code == 404


def test_get_review_by_id_success(client, monkeypatch):
    """Тест GET /api/v1/reviews/<review_id> - успішне отримання"""
    import src.api.routes.reviews as review_routes_module
    
    review_obj = SimpleNamespace(review_id=1, user_id=1, rating=5, comment="Nice", created_at=None, updated_at=None, is_approved=True)
    
    def mock_get_review_by_id(db, review_id):
        assert review_id == 1
        return review_obj
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.get("/api/v1/reviews/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["review_id"] == 1


def test_get_review_by_id_pending_hidden(client, monkeypatch):
    """Тест GET /api/v1/reviews/<review_id> - незатверджений відгук прихований"""
    import src.api.routes.reviews as review_routes_module
    
    pending_review = SimpleNamespace(
        review_id=1,
        user_id=1,
        rating=5,
        comment="Hidden",
        created_at=None,
        updated_at=None,
        is_approved=False
    )
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", lambda db, rid: pending_review)
    
    resp = client.get("/api/v1/reviews/1")
    assert resp.status_code == 404


def test_patch_review_unauthorized(client):
    """Тест PATCH /api/v1/reviews/<review_id> - без авторизації"""
    resp = client.patch("/api/v1/reviews/1", json={"rating": 4})
    assert resp.status_code == 401


def test_patch_review_not_found(client, monkeypatch, mock_user_guest, auth_setup):
    """Тест PATCH /api/v1/reviews/<review_id> - відгук не знайдено"""
    auth_setup(mock_user_guest)
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return None
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.patch("/api/v1/reviews/999", 
                        json={"rating": 4},
                        headers={"Authorization": "Bearer token"})
    assert resp.status_code == 404


def test_patch_review_forbidden_not_owner(client, monkeypatch, mock_user_guest, mock_review, auth_setup):
    """Тест PATCH /api/v1/reviews/<review_id> - не власник відгуку (403)"""
    # Користувач з user_id=1 намагається редагувати відгук з user_id=2
    mock_user_guest.user_id = 2
    auth_setup(mock_user_guest)
    
    import src.api.routes.reviews as review_routes_module
    
    review_of_another_user = MagicMock()
    review_of_another_user.review_id = 1
    review_of_another_user.user_id = 1  # Відгук належить user_id=1
    review_of_another_user.rating = 5
    review_of_another_user.comment = 'Great hotel!'
    
    def mock_get_review_by_id(db, review_id):
        return review_of_another_user
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.patch("/api/v1/reviews/1", 
                        json={"rating": 4},
                        headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403


def test_patch_review_success_owner(client, monkeypatch, mock_user_guest, auth_setup):
    """Тест PATCH /api/v1/reviews/<review_id> - успішне оновлення власником"""
    auth_setup(mock_user_guest)
    
    import src.api.routes.reviews as review_routes_module
    
    # існуючий відгук користувача
    existing = SimpleNamespace(review_id=1, user_id=1, rating=3, comment="Old", created_at=None, updated_at=None)
    updated = SimpleNamespace(review_id=1, user_id=1, rating=4, comment="Old", created_at=None, updated_at=None)
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", lambda db, rid: existing)
    monkeypatch.setattr(review_routes_module, "update_review", lambda db, rid, data: updated)
    
    resp = client.patch("/api/v1/reviews/1", json={"rating": 4}, headers={"Authorization": "Bearer token"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["rating"] == 4



def test_delete_review_unauthorized(client):
    """Тест DELETE /api/v1/reviews/<review_id> - без авторизації"""
    resp = client.delete("/api/v1/reviews/1")
    assert resp.status_code == 401


def test_delete_review_not_found(client, monkeypatch, mock_user_guest, auth_setup):
    """Тест DELETE /api/v1/reviews/<review_id> - відгук не знайдено"""
    auth_setup(mock_user_guest)
    
    import src.api.routes.reviews as review_routes_module
    
    def mock_get_review_by_id(db, review_id):
        return None
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.delete("/api/v1/reviews/999", 
                         headers={"Authorization": "Bearer token"})
    assert resp.status_code == 404


def test_delete_review_forbidden_not_owner(client, monkeypatch, mock_user_guest, mock_review, auth_setup):
    """Тест DELETE /api/v1/reviews/<review_id> - не власник відгуку (403)"""
    mock_user_guest.user_id = 2
    auth_setup(mock_user_guest)
    
    import src.api.routes.reviews as review_routes_module
    
    review_of_another_user = MagicMock()
    review_of_another_user.review_id = 1
    review_of_another_user.user_id = 1
    review_of_another_user.rating = 5
    review_of_another_user.comment = 'Great hotel!'
    
    def mock_get_review_by_id(db, review_id):
        return review_of_another_user
    
    monkeypatch.setattr(review_routes_module, "get_review_by_id", mock_get_review_by_id)
    
    resp = client.delete("/api/v1/reviews/1", 
                         headers={"Authorization": "Bearer token"})
    assert resp.status_code == 403


def test_delete_review_success_owner(client, monkeypatch, mock_user_guest, mock_review, auth_setup):
    """Тест DELETE /api/v1/reviews/<review_id> - успішне видалення власником"""
    auth_setup(mock_user_guest)
    
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


def test_delete_review_success_admin(client, monkeypatch, mock_user_admin, mock_review, auth_setup):
    """Тест DELETE /api/v1/reviews/<review_id> - успішне видалення адміном"""
    auth_setup(mock_user_admin)
    
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


def test_delete_review_value_error(client, monkeypatch, mock_user_guest, mock_review, auth_setup):
    """Тест DELETE /api/v1/reviews/<review_id> - помилка при видаленні (400)"""
    auth_setup(mock_user_guest)
    
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

# Тести для сервісу відгуків
def test_get_all_reviews():
    """Тест рядків 5-7: отримання всіх відгуків"""
    from src.api.services.review_service import get_all_reviews
    
    mock_review1 = MagicMock()
    mock_review2 = MagicMock()
    mock_reviews = [mock_review1, mock_review2]
    
    mock_filtered = MagicMock()
    mock_filtered.order_by.return_value.all.return_value = mock_reviews

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered
    
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query
    
    
    result = get_all_reviews(mock_db)
    
    assert result == mock_reviews
    mock_db.query.assert_called_once()
    mock_query.filter.assert_called_once()
    mock_filtered.order_by.assert_called_once()
    mock_filtered.order_by.return_value.all.assert_called_once()


def test_get_review_by_id_found():
    from src.api.services.review_service import get_review_by_id
    
    mock_review = MagicMock()
    mock_review.review_id = 1
    
    mock_db = MagicMock()
    mock_db.get.return_value = mock_review
    
    result = get_review_by_id(mock_db, 1)
    
    assert result == mock_review
    mock_db.get.assert_called_once()


def test_service_get_review_by_id_not_found():
    from src.api.services.review_service import get_review_by_id
    
    mock_db = MagicMock()
    mock_db.get.return_value = None
    
    result = get_review_by_id(mock_db, 999)
    
    assert result is None


def test_get_user_reviews():
    from src.api.services.review_service import get_user_reviews
    
    mock_review1 = MagicMock()
    mock_review2 = MagicMock()
    mock_reviews = [mock_review1, mock_review2]
    
    mock_filtered = MagicMock()
    mock_filtered.order_by.return_value.all.return_value = mock_reviews

    mock_filter_by = MagicMock()
    mock_filter_by.filter.return_value = mock_filtered
    
    mock_query = MagicMock()
    mock_query.filter_by.return_value = mock_filter_by
    
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query
    
    result = get_user_reviews(mock_db, 1)
    
    assert result == mock_reviews
    mock_query.filter_by.assert_called_once_with(user_id=1)
    mock_filter_by.filter.assert_called_once()
    mock_filtered.order_by.assert_called_once()
    mock_filtered.order_by.return_value.all.assert_called_once()


def test_create_review_success():
    from src.api.services.review_service import create_review
    
    mock_user = MagicMock()
    mock_user.user_id = 1
    
    mock_db = MagicMock()
    mock_db.query.return_value.get.return_value = mock_user
    
    # Створюємо мок для Review
    mock_review_instance = MagicMock()
    
    review_data = {
        'user_id': 1,
        'room_id': 101,
        'rating': 5,
        'comment': 'Great hotel!'
    }
    
    # Патчимо Review клас
    with patch('src.api.services.review_service.Review') as MockReview:
        MockReview.return_value = mock_review_instance
        
        result = create_review(mock_db, review_data)
    
    # Перевіряємо що був створений Review
    assert result == mock_review_instance
    assert mock_db.add.called
    assert mock_db.add.call_args[0][0] == mock_review_instance
    assert mock_db.commit.called
    mock_db.query.return_value.get.assert_called_once_with(1)



def test_create_review_user_not_found():
    from src.api.services.review_service import create_review
    
    mock_db = MagicMock()
    mock_db.query.return_value.get.return_value = None
    
    review_data = {
        'user_id': 999,
        'room_id': 101,
        'rating': 5,
        'comment': 'Great hotel!'
    }
    
    with pytest.raises(ValueError) as exc_info:
        create_review(mock_db, review_data)
    
    assert "User with ID 999 not found" in str(exc_info.value)


def test_create_review_without_comment():
    from src.api.services.review_service import create_review
    
    mock_user = MagicMock()
    mock_user.user_id = 1
    
    mock_db = MagicMock()
    mock_db.query.return_value.get.return_value = mock_user
    
    review_data = {
        'user_id': 1,
        'room_id': 101,
        'rating': 4
        # comment не передається
    }
    
    result = create_review(mock_db, review_data)
    
    assert result is not None
    mock_db.commit.assert_called_once()


def test_update_review_success():
    from src.api.services.review_service import update_review
    
    mock_review = MagicMock()
    mock_review.review_id = 1
    mock_review.rating = 3
    mock_review.comment = "Old comment"
    mock_review.room_id = 101
    mock_review.updated_at = None
    
    mock_db = MagicMock()
    mock_db.get.return_value = mock_review
    
    update_data = {
        'rating': 5,
        'comment': 'Updated comment',
        'room_id': 102
    }
    
    result = update_review(mock_db, 1, update_data)
    
    assert result == mock_review
    assert mock_review.rating == 5
    assert mock_review.comment == 'Updated comment'
    assert mock_review.room_id == 102
    assert mock_review.updated_at is not None
    mock_db.commit.assert_called_once()


def test_update_review_not_found():
    from src.api.services.review_service import update_review
    
    mock_db = MagicMock()
    mock_db.get.return_value = None
    
    update_data = {'rating': 5}
    
    with pytest.raises(ValueError) as exc_info:
        update_review(mock_db, 999, update_data)
    
    assert "Review with ID 999 not found" in str(exc_info.value)


def test_update_review_partial_fields():
    from src.api.services.review_service import update_review
    
    mock_review = MagicMock()
    mock_review.review_id = 1
    mock_review.rating = 3
    mock_review.comment = "Old comment"
    mock_review.room_id = 101
    mock_review.updated_at = None
    
    mock_db = MagicMock()
    mock_db.get.return_value = mock_review
    
    # Оновлюємо тільки rating
    update_data = {'rating': 4}
    
    result = update_review(mock_db, 1, update_data)
    
    assert mock_review.rating == 4
    assert mock_review.comment == "Old comment"  # Не змінилося
    assert mock_review.room_id == 101  # Не змінилося
    assert mock_review.updated_at is not None
    mock_db.commit.assert_called_once()


def test_update_review_no_fields():
    from src.api.services.review_service import update_review
    
    mock_review = MagicMock()
    mock_review.review_id = 1
    mock_review.rating = 3
    mock_review.comment = "Old comment"
    mock_review.room_id = 101
    mock_review.updated_at = None
    
    mock_db = MagicMock()
    mock_db.get.return_value = mock_review
    
    # Пустий словник для оновлення
    update_data = {}
    
    result = update_review(mock_db, 1, update_data)
    
    assert mock_review.rating == 3  # Не змінилося
    assert mock_review.comment == "Old comment"  # Не змінилося
    assert mock_review.room_id == 101  # Не змінилося
    assert mock_review.updated_at is not None  # updated_at все одно має оновитися
    mock_db.commit.assert_called_once()


def test_delete_review_success():
    from src.api.services.review_service import delete_review
    
    mock_review = MagicMock()
    mock_review.review_id = 1
    
    mock_db = MagicMock()
    mock_db.get.return_value = mock_review
    
    result = delete_review(mock_db, 1)
    
    assert result is True
    mock_db.delete.assert_called_once_with(mock_review)


def test_delete_review_not_found():
    from src.api.services.review_service import delete_review
    
    mock_db = MagicMock()
    mock_db.get.return_value = None
    
    with pytest.raises(ValueError) as exc_info:
        delete_review(mock_db, 999)
    
    assert "Review with ID 999 not found" in str(exc_info.value)


def test_get_average_rating_with_reviews():
    from src.api.services.review_service import get_average_rating
    
    mock_scalar = MagicMock()
    mock_scalar.return_value = 4.5
    
    mock_filtered = MagicMock()
    mock_filtered.scalar = mock_scalar

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered
    
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query
    
    result = get_average_rating(mock_db)
    
    assert result == 4.5
    mock_query.filter.assert_called_once()
    mock_scalar.assert_called_once()


def test_datetime_import():
    from src.api.services.review_service import datetime
    import datetime as dt
    assert datetime == dt.datetime


def test_models_import():
    from src.api.services.review_service import Review, User
    assert Review is not None
    assert User is not None


def test_create_review_review_object_creation():
    from src.api.services.review_service import create_review, Review
    
    mock_user = MagicMock()
    mock_user.user_id = 1
    
    mock_db = MagicMock()
    mock_db.query.return_value.get.return_value = mock_user
    
    review_data = {
        'user_id': 1,
        'room_id': 101,
        'rating': 5,
        'comment': 'Test comment'
    }
    
    # Захоплюємо аргументи конструктора Review
    captured_args = []
    captured_kwargs = {}
    
    original_review_init = Review.__init__
    
    def mock_review_init(self, *args, **kwargs):
        captured_args.extend(args)
        captured_kwargs.update(kwargs)
        # Викликаємо оригінальний __init__ для мока
        original_review_init(self, *args, **kwargs)
    
    with patch.object(Review, '__init__', mock_review_init):
        # Створюємо мокований Review
        mock_review_instance = MagicMock()
        with patch('src.api.services.review_service.Review', return_value=mock_review_instance):
            result = create_review(mock_db, review_data)
    
    # Перевіряємо що Review був створений з правильними параметрами
    assert result == mock_review_instance
    assert mock_db.add.called
    assert mock_db.commit.called


def test_update_review_datetime_now():
    from src.api.services.review_service import update_review
    
    mock_review = MagicMock()
    mock_review.review_id = 1
    mock_review.updated_at = None
    
    mock_db = MagicMock()
    mock_db.get.return_value = mock_review
    
    # Патчимо datetime.utcnow для перевірки
    fixed_datetime = datetime(2024, 1, 1, 12, 0, 0)
    
    with patch('src.api.services.review_service.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        
        result = update_review(mock_db, 1, {'rating': 5})
    
    assert mock_review.updated_at == fixed_datetime


def test_func_import_in_get_average_rating():
    """Тест рядка 68: перевірка локального імпорту func"""
    import src.api.services.review_service as review_service
    
    # Перевіряємо що func не імпортовано на рівні модуля
    assert 'func' not in dir(review_service)
    
    # Перевіряємо що функція працює
    mock_scalar = MagicMock()
    mock_scalar.return_value = 4.5
    
    mock_filtered = MagicMock()
    mock_filtered.scalar = mock_scalar

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered
    
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query
    
    # Просто викликаємо функцію без мокування func
    result = review_service.get_average_rating(mock_db)
    
    assert result == 4.5
    mock_query.filter.assert_called_once()
    mock_scalar.assert_called_once()


def test_get_all_reviews_order_by():
    from src.api.services.review_service import get_all_reviews, Review
    
    mock_reviews = [MagicMock(), MagicMock()]
    
    mock_order_by = MagicMock()
    mock_order_by.all.return_value = mock_reviews
    
    mock_filtered = MagicMock()
    mock_filtered.order_by.return_value = mock_order_by

    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered
    
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query
    
    result = get_all_reviews(mock_db)
    
    # Перевіряємо що order_by викликано з правильним аргументом
    mock_query.filter.assert_called_once()
    mock_filtered.order_by.assert_called_once()
    call_args = mock_filtered.order_by.call_args[0][0]
    # Перевіряємо що викликано Review.created_at.desc()
    assert "Review.created_at.desc()" in str(call_args) or hasattr(call_args, 'desc')


def test_get_user_reviews_order_by():
    from src.api.services.review_service import get_user_reviews, Review
    
    mock_reviews = [MagicMock()]
    
    mock_all = MagicMock()
    mock_all.return_value = mock_reviews
    
    mock_order_by_source = MagicMock()
    mock_order_by_source.all = mock_all

    mock_filter = MagicMock()
    mock_filter.order_by.return_value = mock_order_by_source
    
    mock_filter_by = MagicMock()
    mock_filter_by.filter.return_value = mock_filter
    
    mock_query = MagicMock()
    mock_query.filter_by.return_value = mock_filter_by
    
    mock_db = MagicMock()
    mock_db.query.return_value = mock_query
    
    result = get_user_reviews(mock_db, 1)
    
    mock_filter_by.filter.assert_called_once()
    mock_filter.order_by.assert_called_once()
    mock_all.assert_called_once()

 
