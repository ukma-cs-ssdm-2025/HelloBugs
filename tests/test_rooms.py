import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from src.api.services.room_service import (
    get_all_rooms, get_room_by_id, create_room,
    update_room_partial, update_room_full, delete_room,
    get_room_with_amenities, get_rooms_by_type
)
from src.api.models.room_model import Room, RoomType, RoomStatus, Amenity, RoomAmenity
import uuid
import math

@pytest.fixture
def test_room_data():
    return {
        "room_number": f"Room_{uuid.uuid4().hex[:6]}",
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 1500.0,
        "status": "AVAILABLE",
        "floor": 2,
        "size_sqm": 25.0,
        "description": "Cozy light room"
    }


@pytest.fixture
def existing_room(db_session, test_room_data):
    room = create_room(db_session, test_room_data)
    db_session.commit()
    return room


@pytest.fixture
def test_amenity(db_session):
    amenity = Amenity(
        amenity_name="WiFi",
        icon_url="http://example.com/wifi.jpg"
    )
    db_session.add(amenity)
    db_session.commit()
    return amenity


def test_create_room_success(db_session, test_room_data):
    room = create_room(db_session, test_room_data)
    db_session.commit()

    assert room is not None
    assert room.room_id is not None
    assert room.room_number == test_room_data["room_number"]
    assert room.room_type == RoomType.STANDARD
    assert room.max_guest == test_room_data["max_guest"]
    assert room.base_price == test_room_data["base_price"]
    assert room.status == RoomStatus.AVAILABLE


def test_create_room_duplicate_number(db_session, existing_room):
    duplicate_data = {
        "room_number": existing_room.room_number,
        "room_type": "DELUXE",
        "max_guest": 3,
        "base_price": 2000.0,
        "status": "AVAILABLE",
        "floor": 3,
        "size_sqm": 30.0,
        "description": "Duplicate room"
    }

    with pytest.raises(ValueError, match=f"Room with number {existing_room.room_number} already exists"):
        create_room(db_session, duplicate_data)


def test_create_room_invalid_type(db_session):
    invalid_data = {
        "room_number": f"Invalid_{uuid.uuid4().hex[:6]}",
        "room_type": "INVALID_TYPE",
        "max_guest": 2,
        "base_price": 1500.0,
        "status": "AVAILABLE",
        "floor": 2,
        "size_sqm": 25.0
    }

    with pytest.raises(ValueError, match="Invalid room_type"):
        create_room(db_session, invalid_data)


def test_create_room_invalid_status(db_session):
    invalid_data = {
        "room_number": f"Invalid_{uuid.uuid4().hex[:6]}",
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 1500.0,
        "status": "INVALID_STATUS",
        "floor": 2,
        "size_sqm": 25.0
    }

    with pytest.raises(ValueError, match="Invalid status"):
        create_room(db_session, invalid_data)


def test_get_all_rooms(db_session, existing_room):
    rooms = get_all_rooms(db_session)
    assert isinstance(rooms, list)
    assert len(rooms) > 0
    assert any(room.room_id == existing_room.room_id for room in rooms)


def test_update_room_partial(db_session, existing_room):
    update_data = {
        "base_price": 1700.0,
        "status": "MAINTENANCE",
        "description": "Updated description"
    }

    updated_room = update_room_partial(db_session, existing_room.room_id, update_data)
    db_session.commit()

    assert math.isclose(updated_room.base_price, 1700.0, rel_tol=1e-9, abs_tol=1e-9)
    assert updated_room.status == RoomStatus.MAINTENANCE
    assert updated_room.description == "Updated description"


def test_delete_room(db_session, existing_room):
    result = delete_room(db_session, existing_room.room_id)
    db_session.commit()

    assert result is True
    deleted_room = get_room_by_id(db_session, existing_room.room_id)
    assert deleted_room is None


def test_update_room_partial_not_found(db_session):
    result = update_room_partial(db_session, 999999, {"base_price": 2000.0})
    assert result is None


def test_update_room_partial_change_room_number(db_session, existing_room):
    new_number = f"NewRoom_{uuid.uuid4().hex[:6]}"
    update_data = {"room_number": new_number}

    updated_room = update_room_partial(db_session, existing_room.room_id, update_data)
    db_session.commit()

    assert updated_room.room_number == new_number


def test_update_room_partial_duplicate_room_number(db_session):
    room1_data = {
        "room_number": f"Room1_{uuid.uuid4().hex[:6]}",
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 1500.0,
        "floor": 1,
        "size_sqm": 25.0
    }
    room2_data = {
        "room_number": f"Room2_{uuid.uuid4().hex[:6]}",
        "room_type": "DELUXE",
        "max_guest": 3,
        "base_price": 2000.0,
        "floor": 2,
        "size_sqm": 30.0
    }

    room1 = create_room(db_session, room1_data)
    room2 = create_room(db_session, room2_data)
    db_session.commit()

    with pytest.raises(ValueError, match="already exists"):
        update_room_partial(db_session, room2.room_id, {"room_number": room1.room_number})


def test_update_room_partial_invalid_room_type(db_session, existing_room):
    with pytest.raises(ValueError, match="Invalid room_type"):
        update_room_partial(db_session, existing_room.room_id, {"room_type": "INVALID"})


def test_update_room_partial_invalid_status(db_session, existing_room):
    with pytest.raises(ValueError, match="Invalid status"):
        update_room_partial(db_session, existing_room.room_id, {"status": "INVALID"})


def test_update_room_partial_with_amenities(db_session, existing_room, test_amenity):
    update_data = {
        "amenities": [test_amenity.amenity_id]
    }

    updated_room = update_room_partial(db_session, existing_room.room_id, update_data)
    db_session.commit()

    room_amenities = db_session.query(RoomAmenity).filter_by(room_id=existing_room.room_id).all()
    assert len(room_amenities) == 1
    assert room_amenities[0].amenity_id == test_amenity.amenity_id


def test_update_room_partial_integrity_error(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=IntegrityError("", "", "")):
        with pytest.raises(ValueError, match="Room number already exists"):
            update_room_partial(db_session, existing_room.room_id, {"base_price": 2000.0})


def test_update_room_partial_sqlalchemy_error(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("DB Error")):
        with pytest.raises(Exception, match="Database error"):
            update_room_partial(db_session, existing_room.room_id, {"base_price": 2000.0})


def test_update_room_partial_generic_exception(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=Exception("Unexpected")):
        with pytest.raises(Exception):
            update_room_partial(db_session, existing_room.room_id, {"base_price": 2000.0})


def test_update_room_full_not_found(db_session):
    result = update_room_full(db_session, 999999, {"room_number": "Test"})
    assert result is None


def test_update_room_full_invalid_room_type(db_session, existing_room):
    update_data = {
        "room_number": "Test",
        "room_type": "INVALID_TYPE",
        "max_guest": 2,
        "base_price": 1500.0
    }

    with pytest.raises(ValueError, match="Invalid room_type"):
        update_room_full(db_session, existing_room.room_id, update_data)


def test_update_room_full_invalid_status(db_session, existing_room):
    update_data = {
        "room_number": "Test",
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 1500.0,
        "status": "INVALID_STATUS"
    }

    with pytest.raises(ValueError, match="Invalid status"):
        update_room_full(db_session, existing_room.room_id, update_data)


def test_update_room_full_integrity_error(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=IntegrityError("", "", "")):
        update_data = {
            "room_number": "Test",
            "room_type": "STANDARD",
            "max_guest": 2,
            "base_price": 1500.0
        }
        with pytest.raises(ValueError, match="Room number already exists"):
            update_room_full(db_session, existing_room.room_id, update_data)


def test_update_room_full_sqlalchemy_error(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("DB Error")):
        update_data = {
            "room_number": "Test",
            "room_type": "STANDARD",
            "max_guest": 2,
            "base_price": 1500.0
        }
        with pytest.raises(Exception, match="Database error"):
            update_room_full(db_session, existing_room.room_id, update_data)


def test_delete_room_not_found(db_session):
    result = delete_room(db_session, 999999)
    assert result is False


def test_delete_room_sqlalchemy_error(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=SQLAlchemyError("DB Error")):
        with pytest.raises(Exception, match="Database error"):
            delete_room(db_session, existing_room.room_id)


def test_delete_room_generic_exception(db_session, existing_room):
    with patch.object(db_session, 'commit', side_effect=Exception("Unexpected")):
        with pytest.raises(Exception):
            delete_room(db_session, existing_room.room_id)


def test_get_room_with_amenities(db_session, existing_room):
    room = get_room_with_amenities(db_session, existing_room.room_id)
    assert room is not None
    assert room.room_id == existing_room.room_id


def test_get_room_with_amenities_not_found(db_session):
    room = get_room_with_amenities(db_session, 999999)
    assert room is None


def test_get_room_with_amenities_sqlalchemy_error(db_session):
    with patch.object(db_session, 'query', side_effect=SQLAlchemyError("DB Error")):
        with pytest.raises(Exception, match="Database error"):
            get_room_with_amenities(db_session, 1)


def test_get_rooms_by_type_with_enum(db_session, existing_room):
    rooms = get_rooms_by_type(db_session, RoomType.STANDARD)
    assert all(room.room_type == RoomType.STANDARD for room in rooms)


def test_get_rooms_by_type_sqlalchemy_error(db_session):
    with patch.object(db_session, 'query', side_effect=SQLAlchemyError("DB Error")):
        with pytest.raises(Exception, match="Database error"):
            get_rooms_by_type(db_session, "STANDARD")


# ==================== НОВІ ТЕСТИ ДЛЯ API ENDPOINTS ====================

@pytest.fixture
def client(app):
    """Flask test client"""
    return app.test_client()


@pytest.fixture
def sample_room(db_session):
    """Create a sample room for API testing"""
    room = Room(
        room_number=f"API_R{uuid.uuid4().hex[:6]}",
        room_type=RoomType.STANDARD,
        max_guest=2,
        base_price=1500.0,
        status=RoomStatus.AVAILABLE,
        floor=2,
        size_sqm=25.0,
        description="Test room"
    )
    db_session.add(room)
    db_session.commit()
    return room


@pytest.fixture
def sample_amenity(db_session):
    """Create a sample amenity for testing"""
    amenity = Amenity(
        amenity_name=f"Amenity_{uuid.uuid4().hex[:6]}",
        icon_url="http://example.com/icon.png"
    )
    db_session.add(amenity)
    db_session.commit()
    return amenity


# ==================== RoomList GET tests (lines 57-110) ====================

def test_api_get_rooms_no_filters(client, sample_room):
    """Test GET /api/v1/rooms/ without filters"""
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_api_get_rooms_with_room_type_filter(client, sample_room):
    """Test filtering by room_type"""
    response = client.get("/api/v1/rooms/?room_type=STANDARD")
    assert response.status_code == 200
    data = response.get_json()
    assert all(room["room_type"] == "STANDARD" for room in data)


def test_api_get_rooms_with_invalid_room_type(client):
    """Test invalid room_type filter"""
    response = client.get("/api/v1/rooms/?room_type=INVALID")
    assert response.status_code == 400


def test_api_get_rooms_with_price_filters(client, sample_room):
    """Test filtering by min_price and max_price"""
    response = client.get("/api/v1/rooms/?min_price=1000&max_price=2000")
    assert response.status_code == 200


def test_api_get_rooms_with_guests_filter(client, sample_room):
    """Test filtering by guests"""
    response = client.get("/api/v1/rooms/?guests=2")
    assert response.status_code == 200


def test_api_get_rooms_dates_missing_checkout(client):
    """Test date filter with missing check_out"""
    response = client.get("/api/v1/rooms/?check_in=2025-12-01")
    assert response.status_code == 400


def test_api_get_rooms_dates_missing_checkin(client):
    """Test date filter with missing check_in"""
    response = client.get("/api/v1/rooms/?check_out=2025-12-10")
    assert response.status_code == 400


def test_api_get_rooms_invalid_date_format(client):
    """Test invalid date format"""
    response = client.get("/api/v1/rooms/?check_in=invalid&check_out=2025-12-10")
    assert response.status_code == 400


def test_api_get_rooms_checkout_before_checkin(client):
    """Test check_out before check_in"""
    response = client.get("/api/v1/rooms/?check_in=2025-12-10&check_out=2025-12-05")
    assert response.status_code == 400


def test_api_get_rooms_exception_handling(client, monkeypatch):
    """Test exception handling in GET rooms"""

    def mock_error(*args, **kwargs):
        raise Exception("Database error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "get_all_rooms", mock_error)

    with pytest.raises(Exception, match="Database error"):
        client.get("/api/v1/rooms/")


def test_api_get_room_by_id_success(client, sample_room):
    """Test GET /api/v1/rooms/<id> success"""
    response = client.get(f"/api/v1/rooms/{sample_room.room_id}")
    assert response.status_code == 200


def test_api_get_room_by_id_not_found(client):
    """Test GET room with non-existent ID"""
    response = client.get("/api/v1/rooms/999999")
    assert response.status_code == 404


def test_api_patch_room_success(client, sample_room):
    """Test PATCH /api/v1/rooms/<id> success"""
    update_data = {"base_price": 1800.0}
    response = client.patch(f"/api/v1/rooms/{sample_room.room_id}", json=update_data)
    assert response.status_code == 200


def test_api_patch_room_not_found(client):
    """Test PATCH non-existent room"""
    response = client.patch("/api/v1/rooms/999999", json={"base_price": 2000.0})
    assert response.status_code == 404


def test_api_delete_room_success(client, sample_room):
    """Test DELETE /api/v1/rooms/<id> success"""
    response = client.delete(f"/api/v1/rooms/{sample_room.room_id}")
    assert response.status_code == 204


def test_api_delete_room_not_found(client):
    """Test DELETE non-existent room"""
    response = client.delete("/api/v1/rooms/999999")
    assert response.status_code == 404


def test_api_room_availability_success(client, sample_room):
    """Test GET /api/v1/rooms/<id>/availability"""
    response = client.get(f"/api/v1/rooms/{sample_room.room_id}/availability")
    assert response.status_code == 200
    data = response.get_json()
    assert "room_id" in data
    assert "booked" in data


def test_api_room_availability_with_params(client, sample_room):
    """Test availability with custom date range"""
    response = client.get(
        f"/api/v1/rooms/{sample_room.room_id}/availability?start=2025-12-01&end=2025-12-31"
    )
    assert response.status_code == 200


def test_api_room_availability_not_found(client):
    """Test availability for non-existent room"""
    response = client.get("/api/v1/rooms/999999/availability")
    assert response.status_code == 404


def test_api_get_all_amenities(client, sample_amenity):
    """Test GET /api/v1/amenities/"""
    response = client.get("/api/v1/amenities/")
    assert response.status_code == 200


def test_api_get_all_amenities_exception(client, monkeypatch):
    """Test exception handling in GET amenities"""
    def mock_error(*args, **kwargs):
        raise Exception("Database error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "get_all_amenities", mock_error)

    with pytest.raises(Exception, match="Database error"):
        client.get("/api/v1/amenities/")


def test_api_create_amenity_success(client):
    """Test POST /api/v1/amenities/"""
    amenity_data = {
        "amenity_name": f"New_{uuid.uuid4().hex[:6]}",
        "icon_url": "http://example.com/icon.png"
    }
    response = client.post("/api/v1/amenities/", json=amenity_data)
    assert response.status_code == 201


def test_api_create_amenity_duplicate(client, sample_amenity):
    """Test creating duplicate amenity"""
    amenity_data = {
        "amenity_name": sample_amenity.amenity_name,
        "icon_url": "http://example.com/icon.png"
    }
    response = client.post("/api/v1/amenities/", json=amenity_data)
    assert response.status_code == 409


def test_api_create_amenity_exception(client, monkeypatch):
    """Test exception handling in POST amenity"""

    def mock_error(*args, **kwargs):
        raise Exception("Unexpected error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "create_amenity", mock_error)

    with pytest.raises(Exception, match="Unexpected error"):
        client.post("/api/v1/amenities/", json={"amenity_name": "Test"})


def test_api_get_amenity_by_id_success(client, sample_amenity):
    """Test GET /api/v1/amenities/<id>"""
    response = client.get(f"/api/v1/amenities/{sample_amenity.amenity_id}")
    assert response.status_code == 200


def test_api_get_amenity_by_id_not_found(client):
    """Test GET non-existent amenity"""
    response = client.get("/api/v1/amenities/999999")
    assert response.status_code == 404


def test_api_patch_amenity_success(client, sample_amenity):
    """Test PATCH /api/v1/amenities/<id>"""
    response = client.patch(
        f"/api/v1/amenities/{sample_amenity.amenity_id}",
        json={"amenity_name": f"Updated_{uuid.uuid4().hex[:6]}"}
    )
    assert response.status_code == 200


def test_api_patch_amenity_conflict(client, sample_amenity, db_session):
    """Test PATCH amenity with name conflict"""
    amenity2 = Amenity(amenity_name="CONFLICT_AM", icon_url="url")
    db_session.add(amenity2)
    db_session.commit()

    response = client.patch(
        f"/api/v1/amenities/{sample_amenity.amenity_id}",
        json={"amenity_name": "CONFLICT_AM"}
    )
    assert response.status_code == 409


def test_api_patch_amenity_exception(client, sample_amenity, monkeypatch):
    """Test exception in PATCH amenity"""

    def mock_error(*args, **kwargs):
        raise Exception("Unexpected error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "update_amenity", mock_error)

    with pytest.raises(Exception, match="Unexpected error"):
        client.patch(
            f"/api/v1/amenities/{sample_amenity.amenity_id}",
            json={"amenity_name": "Test"}
        )


def test_api_put_amenity_exception(client, sample_amenity, monkeypatch):
    """Test exception in PUT amenity"""

    def mock_error(*args, **kwargs):
        raise Exception("Unexpected error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "update_amenity", mock_error)

    with pytest.raises(Exception, match="Unexpected error"):
        client.put(
            f"/api/v1/amenities/{sample_amenity.amenity_id}",
            json={"amenity_name": "Test"}
        )


def test_api_delete_amenity_success(client, sample_amenity):
    """Test DELETE /api/v1/amenities/<id>"""
    response = client.delete(f"/api/v1/amenities/{sample_amenity.amenity_id}")
    assert response.status_code == 204


def test_api_delete_amenity_exception(client, sample_amenity, monkeypatch):
    """Test exception in DELETE amenity"""

    def mock_error(*args, **kwargs):
        raise Exception("Unexpected error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "delete_amenity", mock_error)

    with pytest.raises(Exception, match="Unexpected error"):
        client.delete(f"/api/v1/amenities/{sample_amenity.amenity_id}")


def test_api_room_booked_ranges_success(client, sample_room):
    """Test GET /api/v1/rooms/<id>/booked-ranges"""
    response = client.get(f"/api/v1/rooms/{sample_room.room_id}/booked-ranges")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_api_room_booked_ranges_with_params(client, sample_room):
    """Test booked ranges with custom dates"""
    response = client.get(
        f"/api/v1/rooms/{sample_room.room_id}/booked-ranges?start=2025-12-01&end=2025-12-31"
    )
    assert response.status_code == 200


def test_api_room_booked_ranges_invalid_date_format(client, sample_room):
    """Test booked ranges with invalid date format"""
    response = client.get(
        f"/api/v1/rooms/{sample_room.room_id}/booked-ranges?start=invalid"
    )
    assert response.status_code == 400


def test_api_room_booked_ranges_exception(client, sample_room, monkeypatch):
    """Test exception handling in booked ranges"""

    def mock_error(*args, **kwargs):
        raise Exception("Unexpected error")

    import src.api.routes.rooms as rooms_module
    monkeypatch.setattr(rooms_module, "get_room_booked_ranges", mock_error)

    with pytest.raises(Exception, match="Unexpected error"):
        client.get(f"/api/v1/rooms/{sample_room.room_id}/booked-ranges")