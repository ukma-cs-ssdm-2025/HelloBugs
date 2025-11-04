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