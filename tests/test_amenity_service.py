import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from src.api.services.amenity_service import (
    get_all_amenities,
    get_amenity_by_id,
    get_amenity_by_name,
    create_amenity,
    update_amenity,
    delete_amenity
)
from src.api.models.room_model import Amenity


@pytest.fixture
def mock_amenity():
    """Фікстура для мокування amenity"""
    amenity = MagicMock(spec=Amenity)
    amenity.amenity_id = 1
    amenity.amenity_name = "WiFi"
    amenity.icon_url = "wifi.png"
    return amenity


@pytest.fixture
def mock_session():
    """Фікстура для мокування сесії бази даних"""
    return MagicMock()


def test_get_all_amenities_success(mock_session, mock_amenity):
    """Тест успішного отримання всіх amenities"""
    mock_query = MagicMock()
    mock_query.all.return_value = [mock_amenity]
    mock_session.query.return_value = mock_query
    
    result = get_all_amenities(mock_session)
    
    assert len(result) == 1
    assert result[0] == mock_amenity
    mock_session.query.assert_called_once_with(Amenity)


def test_get_all_amenities_sqlalchemy_error(mock_session):
    """Тест обробки SQLAlchemyError в get_all_amenities"""
    mock_session.query().all.side_effect = SQLAlchemyError("Database connection failed")
    
    with pytest.raises(Exception, match="Database error"):
        get_all_amenities(mock_session)


def test_get_all_amenities_empty_list(mock_session):
    """Тест отримання порожнього списку amenities"""
    mock_session.query().all.return_value = []
    
    result = get_all_amenities(mock_session)
    
    assert result == []


def test_get_amenity_by_id_success(mock_session, mock_amenity):
    """Тест успішного отримання amenity за ID"""
    mock_session.query().get.return_value = mock_amenity
    
    result = get_amenity_by_id(mock_session, 1)
    
    assert result == mock_amenity
    mock_session.query().get.assert_called_once_with(1)


def test_get_amenity_by_id_not_found(mock_session):
    """Тест коли amenity не знайдено"""
    mock_session.query().get.return_value = None
    
    result = get_amenity_by_id(mock_session, 999)
    
    assert result is None


def test_get_amenity_by_id_sqlalchemy_error(mock_session):
    """Тест обробки SQLAlchemyError в get_amenity_by_id"""
    mock_session.query().get.side_effect = SQLAlchemyError("Database error")
    
    with pytest.raises(Exception, match="Database error"):
        get_amenity_by_id(mock_session, 1)


def test_get_amenity_by_name_success(mock_session, mock_amenity):
    """Тест успішного отримання amenity за назвою"""
    mock_session.query().filter_by().first.return_value = mock_amenity
    
    result = get_amenity_by_name(mock_session, "WiFi")
    
    assert result == mock_amenity


def test_get_amenity_by_name_not_found(mock_session):
    """Тест коли amenity не знайдено за назвою"""
    mock_session.query().filter_by().first.return_value = None
    
    result = get_amenity_by_name(mock_session, "NonExistent")
    
    assert result is None


def test_get_amenity_by_name_sqlalchemy_error(mock_session):
    """Тест обробки SQLAlchemyError в get_amenity_by_name"""
    mock_session.query().filter_by().first.side_effect = SQLAlchemyError("Database error")
    
    with pytest.raises(Exception, match="Database error"):
        get_amenity_by_name(mock_session, "WiFi")


def test_create_amenity_success(mock_session):
    """Тест успішного створення amenity"""
    data = {
        'amenity_name': 'Pool',
        'icon_url': 'pool.png'
    }
    
    mock_session.query().filter_by().first.return_value = None
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        result = create_amenity(mock_session, data)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_create_amenity_already_exists(mock_session, mock_amenity):
    """Тест створення amenity з існуючою назвою"""
    data = {
        'amenity_name': 'WiFi',
        'icon_url': 'wifi.png'
    }
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=mock_amenity):
        with pytest.raises(ValueError, match="already exists"):
            create_amenity(mock_session, data)
    
    mock_session.rollback.assert_called_once()


def test_create_amenity_sqlalchemy_error(mock_session):
    """Тест обробки SQLAlchemyError при створенні amenity"""
    data = {
        'amenity_name': 'Gym',
        'icon_url': 'gym.png'
    }
    
    mock_session.query().filter_by().first.return_value = None
    mock_session.add.side_effect = SQLAlchemyError("Database error")
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        with pytest.raises(Exception, match="Database error"):
            create_amenity(mock_session, data)
    
    mock_session.rollback.assert_called()


def test_create_amenity_generic_exception(mock_session):
    """Тест обробки загального Exception при створенні amenity"""
    data = {
        'amenity_name': 'Spa',
        'icon_url': 'spa.png'
    }
    
    mock_session.query().filter_by().first.return_value = None
    mock_session.commit.side_effect = Exception("Unexpected error")
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        with pytest.raises(Exception, match="Unexpected error"):
            create_amenity(mock_session, data)
    
    mock_session.rollback.assert_called()


def test_update_amenity_not_found(mock_session):
    """Тест оновлення неіснуючого amenity (рядок 68-69)"""
    mock_session.query().get.return_value = None
    
    result = update_amenity(mock_session, 999, {'amenity_name': 'Updated'})
    
    assert result is None


def test_update_amenity_success_no_name_change(mock_session, mock_amenity):
    """Тест успішного оновлення amenity без зміни назви"""
    data = {'icon_url': 'new_wifi.png'}
    
    mock_session.query().get.return_value = mock_amenity
    
    result = update_amenity(mock_session, 1, data)
    
    assert result == mock_amenity
    mock_session.commit.assert_called_once()


def test_update_amenity_success_with_name_change(mock_session, mock_amenity):
    """Тест успішного оновлення amenity зі зміною назви (рядок 71)"""
    data = {'amenity_name': 'WiFi Premium'}
    
    mock_session.query().get.return_value = mock_amenity
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        result = update_amenity(mock_session, 1, data)
    
    assert result == mock_amenity
    mock_session.commit.assert_called_once()


def test_update_amenity_name_already_exists(mock_session, mock_amenity):
    """Тест оновлення amenity з існуючою назвою (рядок 71-73)"""
    data = {'amenity_name': 'Pool'}
    
    mock_session.query().get.return_value = mock_amenity
    
    existing_amenity = MagicMock()
    existing_amenity.amenity_id = 2
    existing_amenity.amenity_name = 'Pool'
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=existing_amenity):
        with pytest.raises(ValueError, match="already exists"):
            update_amenity(mock_session, 1, data)
    
    mock_session.rollback.assert_called()


def test_update_amenity_integrity_error(mock_session, mock_amenity):
    """Тест обробки IntegrityError при оновленні (рядок 83-85)"""
    data = {'amenity_name': 'Updated WiFi'}
    
    mock_session.query().get.return_value = mock_amenity
    mock_session.commit.side_effect = IntegrityError("statement", "params", "orig")
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        with pytest.raises(ValueError, match="Amenity name already exists"):
            update_amenity(mock_session, 1, data)
    
    mock_session.rollback.assert_called()


def test_update_amenity_sqlalchemy_error(mock_session, mock_amenity):
    """Тест обробки SQLAlchemyError при оновленні (рядок 89-92)"""
    data = {'icon_url': 'new_icon.png'}
    
    mock_session.query().get.return_value = mock_amenity
    mock_session.commit.side_effect = SQLAlchemyError("Database error")
    
    with pytest.raises(Exception, match="Database error"):
        update_amenity(mock_session, 1, data)
    
    mock_session.rollback.assert_called()


def test_update_amenity_generic_exception(mock_session, mock_amenity):
    """Тест обробки загального Exception при оновленні (рядок 93-96)"""
    data = {'icon_url': 'new_icon.png'}
    
    mock_session.query().get.return_value = mock_amenity
    mock_session.commit.side_effect = Exception("Unexpected error")
    
    with pytest.raises(Exception, match="Unexpected error"):
        update_amenity(mock_session, 1, data)
    
    mock_session.rollback.assert_called()


def test_update_amenity_skip_amenity_id_field(mock_session, mock_amenity):
    """Тест що amenity_id не оновлюється"""
    data = {'amenity_id': 999, 'amenity_name': 'Updated'}
    
    mock_session.query().get.return_value = mock_amenity
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        result = update_amenity(mock_session, 1, data)
    
    assert mock_amenity.amenity_id == 1


def test_delete_amenity_success(mock_session, mock_amenity):
    """Тест успішного видалення amenity"""
    mock_session.query().get.return_value = mock_amenity
    
    result = delete_amenity(mock_session, 1)
    
    assert result is True
    mock_session.delete.assert_called_once_with(mock_amenity)
    mock_session.commit.assert_called_once()


def test_delete_amenity_not_found(mock_session):
    """Тест видалення неіснуючого amenity (рядок 103-104)"""
    mock_session.query().get.return_value = None
    
    result = delete_amenity(mock_session, 999)
    
    assert result is False
    mock_session.delete.assert_not_called()


def test_delete_amenity_sqlalchemy_error(mock_session, mock_amenity):
    """Тест обробки SQLAlchemyError при видаленні (рядок 111-114)"""
    mock_session.query().get.return_value = mock_amenity
    mock_session.delete.side_effect = SQLAlchemyError("Database error")
    
    with pytest.raises(Exception, match="Database error"):
        delete_amenity(mock_session, 1)
    
    mock_session.rollback.assert_called()


def test_delete_amenity_generic_exception(mock_session, mock_amenity):
    """Тест обробки загального Exception при видаленні (рядок 115-118)"""
    mock_session.query().get.return_value = mock_amenity
    mock_session.commit.side_effect = Exception("Unexpected error")
    
    with pytest.raises(Exception, match="Unexpected error"):
        delete_amenity(mock_session, 1)
    
    mock_session.rollback.assert_called()


def test_create_amenity_with_none_icon(mock_session):
    """Тест створення amenity без іконки"""
    data = {
        'amenity_name': 'Parking',
        'icon_url': None
    }
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        result = create_amenity(mock_session, data)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_create_amenity_missing_icon_url(mock_session):
    """Тест створення amenity без поля icon_url"""
    data = {
        'amenity_name': 'Restaurant'
    }
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        result = create_amenity(mock_session, data)
    
    mock_session.add.assert_called_once()


def test_update_amenity_multiple_fields(mock_session, mock_amenity):
    """Тест оновлення декількох полів одночасно"""
    data = {
        'amenity_name': 'WiFi Pro',
        'icon_url': 'wifi_pro.png'
    }
    
    mock_session.query().get.return_value = mock_amenity
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=None):
        result = update_amenity(mock_session, 1, data)
    
    assert result == mock_amenity
    mock_session.commit.assert_called_once()


def test_update_amenity_same_name(mock_session, mock_amenity):
    """Тест оновлення amenity з тією ж назвою (не повинно бути помилки)"""
    data = {'amenity_name': 'WiFi', 'icon_url': 'new_wifi.png'}
    
    mock_session.query().get.return_value = mock_amenity
    mock_amenity.amenity_name = 'WiFi'
    
    result = update_amenity(mock_session, 1, data)
    
    assert result == mock_amenity


def test_update_amenity_empty_data(mock_session, mock_amenity):
    """Тест оновлення amenity з порожніми даними"""
    data = {}
    
    mock_session.query().get.return_value = mock_amenity
    
    result = update_amenity(mock_session, 1, data)
    
    assert result == mock_amenity
    mock_session.commit.assert_called_once()


def test_get_all_amenities_multiple_results(mock_session):
    """Тест отримання декількох amenities"""
    amenity1 = MagicMock(amenity_id=1, amenity_name="WiFi")
    amenity2 = MagicMock(amenity_id=2, amenity_name="Pool")
    amenity3 = MagicMock(amenity_id=3, amenity_name="Gym")
    
    mock_session.query().all.return_value = [amenity1, amenity2, amenity3]
    
    result = get_all_amenities(mock_session)
    
    assert len(result) == 3
    assert result[0].amenity_name == "WiFi"
    assert result[1].amenity_name == "Pool"
    assert result[2].amenity_name == "Gym"


def test_create_amenity_rollback_on_value_error(mock_session, mock_amenity):
    """Тест що rollback викликається при ValueError"""
    data = {
        'amenity_name': 'WiFi',
        'icon_url': 'wifi.png'
    }
    
    with patch('src.api.services.amenity_service.get_amenity_by_name', return_value=mock_amenity):
        try:
            create_amenity(mock_session, data)
        except ValueError:
            pass
    
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_delete_amenity_commits_after_delete(mock_session, mock_amenity):
    """Тест що commit викликається після delete"""
    mock_session.query().get.return_value = mock_amenity
    
    result = delete_amenity(mock_session, 1)
    
    assert result is True
    mock_session.delete.assert_called_once()
    mock_session.commit.assert_called_once()