import pytest
from datetime import datetime
from src.api.services.room_service import (
    get_all_rooms, get_room_by_id, create_room,
    update_room_partial, delete_room, get_room_by_number
)
from src.api.models.room_model import Room, RoomType, RoomStatus
import uuid


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
    assert room.floor == test_room_data["floor"]


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


def test_get_room_by_id(db_session, existing_room):
    found_room = get_room_by_id(db_session, existing_room.room_id)
    assert found_room is not None
    assert found_room.room_id == existing_room.room_id
    assert found_room.room_number == existing_room.room_number


def test_get_room_by_number(db_session, existing_room):
    found_room = get_room_by_number(db_session, existing_room.room_number)
    assert found_room is not None
    assert found_room.room_number == existing_room.room_number
    assert found_room.room_id == existing_room.room_id


def test_update_room_partial(db_session, existing_room):
    update_data = {
        "base_price": 1700.0,
        "status": "MAINTENANCE",
        "description": "Updated description"
    }

    updated_room = update_room_partial(db_session, existing_room.room_id, update_data)
    db_session.commit()

    assert updated_room.base_price == 1700.0
    assert updated_room.status == RoomStatus.MAINTENANCE
    assert updated_room.description == "Updated description"
    assert updated_room.room_number == existing_room.room_number
    assert updated_room.room_type == existing_room.room_type


def test_update_room_change_type(db_session, existing_room):
    update_data = {
        "room_type": "DELUXE"
    }

    updated_room = update_room_partial(db_session, existing_room.room_id, update_data)
    db_session.commit()

    assert updated_room.room_type == RoomType.DELUXE


def test_delete_room(db_session, existing_room):
    result = delete_room(db_session, existing_room.room_id)
    db_session.commit()

    assert result is True

    deleted_room = get_room_by_id(db_session, existing_room.room_id)
    assert deleted_room is None


def test_get_room_by_id_not_found(db_session):
    found_room = get_room_by_id(db_session, 999999)
    assert found_room is None


def test_get_room_by_number_not_found(db_session):
    found_room = get_room_by_number(db_session, "NONEXISTENT")
    assert found_room is None


def test_create_room_all_types(db_session):
    room_types = ["ECONOMY", "STANDARD", "DELUXE"]

    for room_type in room_types:
        room_data = {
            "room_number": f"{room_type}_{uuid.uuid4().hex[:6]}",
            "room_type": room_type,
            "max_guest": 2,
            "base_price": 1500.0,
            "status": "AVAILABLE",
            "floor": 2,
            "size_sqm": 25.0
        }

        room = create_room(db_session, room_data)
        db_session.commit()

        assert room.room_type == RoomType[room_type]


def test_room_status_transitions(db_session, existing_room):
    # AVAILABLE -> OCCUPIED
    update_data1 = {"status": "OCCUPIED"}
    room1 = update_room_partial(db_session, existing_room.room_id, update_data1)
    db_session.commit()
    assert room1.status == RoomStatus.OCCUPIED

    # OCCUPIED -> MAINTENANCE
    update_data2 = {"status": "MAINTENANCE"}
    room2 = update_room_partial(db_session, existing_room.room_id, update_data2)
    db_session.commit()
    assert room2.status == RoomStatus.MAINTENANCE

    # MAINTENANCE -> AVAILABLE
    update_data3 = {"status": "AVAILABLE"}
    room3 = update_room_partial(db_session, existing_room.room_id, update_data3)
    db_session.commit()
    assert room3.status == RoomStatus.AVAILABLE


def test_create_room_missing_required_fields(db_session):
    incomplete_data = {
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 1500.0,
        "status": "AVAILABLE" # без поля floor
    }

    # Це має викликати помилку в SQLAlchemy при спробі коміту
    with pytest.raises(Exception):
        create_room(db_session, incomplete_data)