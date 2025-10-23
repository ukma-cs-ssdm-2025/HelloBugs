import pytest
from datetime import datetime, timedelta, date
from src.api.services.booking_service import (create_booking, get_all_bookings,
                                              get_booking_by_code, cancel_booking,
                                              update_booking_partial, update_booking_full,
                                              get_user_bookings)
from src.api.models.booking_model import Booking, BookingStatus
from src.api.models.room_model import Room, RoomStatus, RoomType
from src.api.models.user_model import User, UserRole
from werkzeug.security import generate_password_hash
import uuid

@pytest.fixture
def test_user_registered(db_session):
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Registered",
        last_name="User",
        phone="+380674567892",
        is_registered=True,
        password=generate_password_hash("testpassword123"),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.flush()
    return user

@pytest.fixture
def test_room(db_session):
    room = Room(
        room_number=f"Room_{uuid.uuid4().hex[:6]}",
        room_type=RoomType.STANDARD,
        base_price=1000.0,
        status=RoomStatus.AVAILABLE,
        max_guest=2,
        floor=1,
        size_sqm=21.0,
        description="Cozy room"
    )
    db_session.add(room)
    db_session.flush()
    return room


@pytest.fixture
def test_booking(db_session, test_user_registered, test_room):
    booking_data = {
        'user_id': test_user_registered.user_id,
        'room_id': test_room.room_id,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3),
        'special_requests': 'Test booking',
        'status': BookingStatus.ACTIVE
    }

    booking = create_booking(db_session, booking_data)
    db_session.commit()
    return booking


def test_create_booking_with_non_registered_user(db_session, test_room):
    """Тест бронювання для гостя (без user_id, тільки email)"""
    booking_data = {
        'room_id': test_room.room_id,
        'check_in_date': date.today() + timedelta(days=2),
        'check_out_date': date.today() + timedelta(days=4),
        'special_requests': 'Test booking for guest',
        'email': f"guest_{uuid.uuid4().hex[:8]}@example.com",
        'first_name': 'Guest',
        'last_name': 'User',
        'phone': '+380501234567'
    }

    booking = create_booking(db_session, booking_data)
    db_session.commit()

    assert booking is not None
    assert booking.booking_code is not None
    assert booking.user_id is not None
    assert booking.room_id == test_room.room_id
    assert booking.user.is_registered == False
    assert booking.user.password is None
    assert booking.user.role is None
    assert booking.status == BookingStatus.ACTIVE


def test_booking_with_registered_user(db_session, test_user_registered, test_room):
    """Тест бронювання для зареєстрованого користувача"""
    booking_data = {
        'user_id': test_user_registered.user_id,
        'room_id': test_room.room_id,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3),
        'special_requests': 'Test booking for registered user',
        'status': BookingStatus.ACTIVE
    }

    booking = create_booking(db_session, booking_data)
    db_session.commit()

    assert booking is not None
    assert booking.booking_code is not None
    assert booking.user_id == test_user_registered.user_id
    assert test_user_registered.is_registered == True
    assert test_user_registered.password is not None
    assert test_user_registered.role is not None
    assert booking.room_id == test_room.room_id
    assert booking.status == BookingStatus.ACTIVE


def test_get_bookings(db_session, test_booking):
    bookings = get_all_bookings(db_session)

    assert isinstance(bookings, list)
    assert len(bookings) > 0


def test_get_booking_by_code(db_session, test_booking):
    booking = get_booking_by_code(db_session, test_booking.booking_code)

    assert booking is not None
    assert booking.booking_code == test_booking.booking_code
    assert booking.status is not None


def test_cancel_booking_success(db_session, test_booking):  # Додав test_booking
    result = cancel_booking(db_session, test_booking.booking_code)
    db_session.commit()

    assert result is True
    cancelled_booking = get_booking_by_code(db_session, test_booking.booking_code)
    assert cancelled_booking.status == BookingStatus.CANCELLED


def test_get_user_bookings(db_session, test_booking, test_user_registered):
    user_bookings = get_user_bookings(db_session, test_user_registered.user_id)

    assert isinstance(user_bookings, list)
    assert len(user_bookings) > 0

    for booking in user_bookings:
        assert booking.user_id == test_user_registered.user_id

    print(f"✅ Знайдено {len(user_bookings)} бронювань для користувача {test_user_registered.user_id}")


def test_get_user_bookings_empty(db_session, test_user_registered):
    new_user = User(
        email=f"new_{uuid.uuid4().hex[:8]}@example.com",
        first_name="New",
        last_name="User",
        phone="+380999999999",
        is_registered=True,
        password=generate_password_hash("password123"),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(new_user)
    db_session.flush()

    user_bookings = get_user_bookings(db_session, new_user.user_id)

    assert isinstance(user_bookings, list)
    assert len(user_bookings) == 0


def test_update_booking_partial(db_session, test_booking):
    update_data = {
        'special_requests': 'Оновлені побажання',
        'status': BookingStatus.ACTIVE
    }

    updated_booking = update_booking_partial(db_session, test_booking.booking_code, update_data)
    db_session.commit()

    assert updated_booking is not None
    assert updated_booking.special_requests == 'Оновлені побажання'
    assert updated_booking.status == BookingStatus.ACTIVE
    assert updated_booking.booking_code == test_booking.booking_code


def test_update_booking_full(db_session, test_booking, test_room):
    another_room = Room(
        room_number=f"Room_another_{uuid.uuid4().hex[:6]}",
        room_type=RoomType.DELUXE,
        base_price=1500.0,
        status=RoomStatus.AVAILABLE,
        max_guest=3,
        floor=2,
        size_sqm=30.0,
        description="Deluxe room"
    )
    db_session.add(another_room)
    db_session.flush()

    update_data = {
        'room_id': another_room.room_id,
        'check_in_date': date.today() + timedelta(days=5),
        'check_out_date': date.today() + timedelta(days=7),
        'special_requests': 'Повністю оновлене бронювання',
        'user_id': test_booking.user_id
    }

    updated_booking = update_booking_full(db_session, test_booking.booking_code, update_data)
    db_session.commit()

    assert updated_booking is not None
    assert updated_booking.room_id == another_room.room_id
    assert updated_booking.check_in_date == update_data['check_in_date']
    assert updated_booking.check_out_date == update_data['check_out_date']
    assert updated_booking.special_requests == 'Повністю оновлене бронювання'


def test_cancel_booking_already_cancelled(db_session, test_booking):
    result1 = cancel_booking(db_session, test_booking.booking_code)
    db_session.commit()
    assert result1 is True

    result2 = cancel_booking(db_session, test_booking.booking_code)
    db_session.commit()

    assert result2 is True

    booking = db_session.query(Booking).get(test_booking.booking_code)
    assert booking.status == BookingStatus.CANCELLED


def test_update_cancelled_booking(db_session, test_booking):
    cancel_booking(db_session, test_booking.booking_code)
    db_session.commit()

    update_data = {
        'special_requests': 'Спроба оновити скасоване'
    }

    with pytest.raises(ValueError, match="Can only change status for completed/cancelled bookings"):
        update_booking_partial(db_session, test_booking.booking_code, update_data)


def test_update_booking_nonexistent(db_session):
    update_data = {'special_requests': 'Тест'}
    result = update_booking_partial(db_session, 'NONEXISTENT123', update_data)

    assert result is None



def test_cancel_nonexistent_booking(db_session):
    result = cancel_booking(db_session, 'NONEXISTENT123')

    assert result is False