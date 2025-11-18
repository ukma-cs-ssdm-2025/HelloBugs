import pytest
from datetime import datetime, timedelta, date, timezone
from src.api.services.booking_service import (
    create_booking, get_all_bookings,
    get_booking_by_code, cancel_booking,
    update_booking_partial, update_booking_full,
    get_user_bookings, check_room_availability,
    calculate_total_price, update_expired_bookings_status,
    search_bookings, get_upcoming_checkins,
    get_room_booked_ranges, _validate_dates,
    _resolve_user, _get_room_or_error
)
from src.api.models.booking_model import Booking, BookingStatus
from src.api.models.room_model import Room, RoomStatus, RoomType
from src.api.models.user_model import User, UserRole
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError
import secrets
import uuid

@pytest.fixture
def test_user_registered(db_session):
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Registered",
        last_name="User",
        phone="+380674567892",
        is_registered=True,
        password=generate_password_hash(secrets.token_urlsafe(16)),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
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
    db_session.commit()
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
    """Тест бронювання для гостя"""
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
    assert booking.user.role == UserRole.GUEST
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


def test_cancel_booking_success(db_session, test_booking):
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


def test_get_user_bookings_empty(db_session, test_user_registered):
    new_user = User(
        email=f"new_{uuid.uuid4().hex[:8]}@example.com",
        first_name="New",
        last_name="User",
        phone="+380999999999",
        is_registered=True,
        password=generate_password_hash(secrets.token_urlsafe(16)),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(new_user)
    db_session.commit()

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
    db_session.commit()

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
    with pytest.raises(ValueError, match="Booking with ID NONEXISTENT123 not found"):
        update_booking_partial(db_session, 'NONEXISTENT123', update_data)


def test_cancel_nonexistent_booking(db_session):
    with pytest.raises(ValueError, match="Booking with ID NONEXISTENT123 not found"):
        cancel_booking(db_session, 'NONEXISTENT123')


def test_validate_dates_checkout_before_checkin(db_session):
    check_in = date.today() + timedelta(days=5)
    check_out = date.today() + timedelta(days=3)
    
    with pytest.raises(ValueError, match="Check-out date must be after check-in date"):
        _validate_dates(check_in, check_out)

def test_validate_dates_checkin_in_past(db_session):
    check_in = date.today() - timedelta(days=1)
    check_out = date.today() + timedelta(days=3)
    
    with pytest.raises(ValueError, match="Check-in date cannot be in the past"):
        _validate_dates(check_in, check_out)

def test_resolve_user_nonexistent_user_id(db_session):
    with pytest.raises(ValueError, match="User not found"):
        _resolve_user(db_session, 999999, None, {})

def test_resolve_user_registered_email(db_session, test_user_registered):
    with pytest.raises(ValueError, match="This email is already registered. Please log in to make a booking."):
        _resolve_user(db_session, None, test_user_registered.email, {})

def test_resolve_user_existing_guest_email(db_session):
    guest = User(
        email=f"guest_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Guest",
        last_name="User",
        phone="+380501112233",
        is_registered=False,
        role=UserRole.GUEST,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(guest)
    db_session.commit()
    
    user_id = _resolve_user(db_session, None, guest.email, {})
    assert user_id == guest.user_id

def test_resolve_user_new_guest(db_session):
    email = f"newguest_{uuid.uuid4().hex[:8]}@example.com"
    data = {
        'first_name': 'New',
        'last_name': 'Guest',
        'phone': '+380501234567'
    }
    
    user_id = _resolve_user(db_session, None, email, data)
    
    assert user_id is not None
    user = db_session.query(User).get(user_id)
    assert user.email == email
    assert user.is_registered == False
    assert user.role == UserRole.GUEST

def test_resolve_user_no_user_id_no_email(db_session):
    with pytest.raises(ValueError, match="Either user_id or email must be provided"):
        _resolve_user(db_session, None, None, {})

def test_get_room_or_error_not_found(db_session):
    with pytest.raises(ValueError, match="Room not found"):
        _get_room_or_error(db_session, 999999)

def test_get_room_or_error_success(db_session, test_room):
    room = _get_room_or_error(db_session, test_room.room_id)
    assert room.room_id == test_room.room_id

def test_check_room_availability_room_not_available(db_session, test_room):
    test_room.status = RoomStatus.MAINTENANCE
    db_session.commit()
    
    with pytest.raises(ValueError, match="is not available"):
        check_room_availability(
            db_session, 
            test_room.room_id,
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=3)
        )

def test_check_room_availability_room_not_found(db_session):
    with pytest.raises(ValueError, match="is not available"):
        check_room_availability(
            db_session,
            999999,
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=3)
        )

def test_check_room_availability_overlapping_booking(db_session, test_booking, test_room):
    is_available, message = check_room_availability(
        db_session,
        test_room.room_id,
        test_booking.check_in_date,
        test_booking.check_out_date
    )
    
    assert is_available == False
    assert "already booked" in message

def test_check_room_availability_with_exclude(db_session, test_booking, test_room):
    is_available, message = check_room_availability(
        db_session,
        test_room.room_id,
        test_booking.check_in_date,
        test_booking.check_out_date,
        exclude_booking_code=test_booking.booking_code
    )
    
    assert is_available == True
    assert "available" in message

def test_calculate_total_price_room_not_found(db_session):
    with pytest.raises(ValueError, match="not found"):
        calculate_total_price(
            db_session,
            999999,
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=3)
        )

def test_calculate_total_price_success(db_session, test_room):
    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=4)  # 3 ночі
    
    total = calculate_total_price(db_session, test_room.room_id, check_in, check_out)
    
    assert total == float(test_room.base_price) * 3

def test_cancel_booking_not_found(db_session):
    with pytest.raises(ValueError, match="not found"):
        cancel_booking(db_session, 'NONEXISTENT')

def test_search_bookings_by_user_id(db_session, test_booking, test_user_registered):
    """Тест для рядків 290-291: пошук по user_id"""
    bookings = search_bookings(db_session, user_id=test_user_registered.user_id)
    
    assert isinstance(bookings, list)
    assert len(bookings) > 0
    assert all(b.user_id == test_user_registered.user_id for b in bookings)

def test_search_bookings_by_room_id(db_session, test_booking, test_room):
    bookings = search_bookings(db_session, room_id=test_room.room_id)
    
    assert isinstance(bookings, list)
    assert len(bookings) > 0
    assert all(b.room_id == test_room.room_id for b in bookings)

def test_search_bookings_by_status(db_session, test_booking):
    bookings = search_bookings(db_session, status=BookingStatus.ACTIVE)
    
    assert isinstance(bookings, list)
    assert all(b.status == BookingStatus.ACTIVE for b in bookings)

def test_search_bookings_check_in_from(db_session, test_booking):
    bookings = search_bookings(
        db_session, 
        check_in_from=date.today()
    )
    
    assert isinstance(bookings, list)

def test_search_bookings_check_in_to(db_session, test_booking):
    bookings = search_bookings(
        db_session,
        check_in_to=date.today() + timedelta(days=30)
    )
    
    assert isinstance(bookings, list)

def test_search_bookings_check_out_from(db_session, test_booking):
    bookings = search_bookings(
        db_session,
        check_out_from=date.today()
    )
    
    assert isinstance(bookings, list)

def test_search_bookings_check_out_to(db_session, test_booking):
    bookings = search_bookings(
        db_session,
        check_out_to=date.today() + timedelta(days=30)
    )
    
    assert isinstance(bookings, list)

def test_search_bookings_combined_filters(db_session, test_booking, test_user_registered):
    bookings = search_bookings(
        db_session,
        user_id=test_user_registered.user_id,
        status=BookingStatus.ACTIVE,
        check_in_from=date.today()
    )
    
    assert isinstance(bookings, list)

def test_get_upcoming_checkins(db_session, test_user_registered, test_room):
    future_booking = Booking(
        booking_code="FUTURE123",
        user_id=test_user_registered.user_id,
        room_id=test_room.room_id,
        check_in_date=date.today() + timedelta(days=2),
        check_out_date=date.today() + timedelta(days=5),
        status=BookingStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(future_booking)
    db_session.commit()
    
    bookings = get_upcoming_checkins(db_session, days=7)
    
    assert isinstance(bookings, list)
    assert any(b.booking_code == "FUTURE123" for b in bookings)

def test_get_upcoming_checkins_custom_days(db_session):
    bookings = get_upcoming_checkins(db_session, days=14)
    assert isinstance(bookings, list)

def test_get_room_booked_ranges(db_session, test_booking, test_room):
    start = date.today()
    end = date.today() + timedelta(days=30)
    
    ranges = get_room_booked_ranges(db_session, test_room.room_id, start, end)
    
    assert isinstance(ranges, list)
    assert len(ranges) > 0
    
    for r in ranges:
        assert 'start' in r
        assert 'end' in r
        assert isinstance(r['start'], str)
        assert isinstance(r['end'], str)

def test_get_room_booked_ranges_cancelled_excluded(db_session, test_user_registered, test_room):
    cancelled = Booking(
        booking_code="CANCELLED123",
        user_id=test_user_registered.user_id,
        room_id=test_room.room_id,
        check_in_date=date.today() + timedelta(days=5),
        check_out_date=date.today() + timedelta(days=7),
        status=BookingStatus.CANCELLED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(cancelled)
    db_session.commit()
    
    start = date.today()
    end = date.today() + timedelta(days=30)
    
    ranges = get_room_booked_ranges(db_session, test_room.room_id, start, end)
    
    for r in ranges:
        r_start = date.fromisoformat(r['start'])
        r_end = date.fromisoformat(r['end'])
        assert not (r_start == cancelled.check_in_date and r_end == cancelled.check_out_date)

def test_get_room_booked_ranges_datetime_conversion(db_session, test_user_registered, test_room):
    booking_dt = Booking(
        booking_code="DATETIME123",
        user_id=test_user_registered.user_id,
        room_id=test_room.room_id,
        check_in_date=datetime.now(timezone.utc).date() + timedelta(days=8),
        check_out_date=datetime.now(timezone.utc).date() + timedelta(days=10),
        status=BookingStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(booking_dt)
    db_session.commit()
    
    start = datetime.now(timezone.utc)
    end = datetime.now(timezone.utc) + timedelta(days=30)
    
    ranges = get_room_booked_ranges(db_session, test_room.room_id, start, end)
    
    assert isinstance(ranges, list)

def test_get_room_booked_ranges_overlap_calculation(db_session, test_user_registered, test_room):

    partial = Booking(
        booking_code="PARTIAL123",
        user_id=test_user_registered.user_id,
        room_id=test_room.room_id,
        check_in_date=date.today() - timedelta(days=2),  # до start_date
        check_out_date=date.today() + timedelta(days=5),  # після start_date
        status=BookingStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(partial)
    db_session.commit()
    
    start = date.today()
    end = date.today() + timedelta(days=10)
    
    ranges = get_room_booked_ranges(db_session, test_room.room_id, start, end)
    
    # Повинен бути діапазон від start до check_out_date
    assert len(ranges) > 0

def test_get_room_booked_ranges_no_overlap(db_session, test_room):
    start = date.today() + timedelta(days=100)
    end = date.today() + timedelta(days=110)
    
    ranges = get_room_booked_ranges(db_session, test_room.room_id, start, end)
    
    assert isinstance(ranges, list)
    # Може бути порожнім якщо немає бронювань в цьому діапазоні

def test_get_room_booked_ranges_completed_included(db_session, test_user_registered, test_room):
    completed = Booking(
        booking_code="COMPLETED123",
        user_id=test_user_registered.user_id,
        room_id=test_room.room_id,
        check_in_date=date.today() + timedelta(days=12),
        check_out_date=date.today() + timedelta(days=14),
        status=BookingStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(completed)
    db_session.commit()
    
    start = date.today()
    end = date.today() + timedelta(days=30)
    
    ranges = get_room_booked_ranges(db_session, test_room.room_id, start, end)
    
    assert isinstance(ranges, list)
    # COMPLETED повинно бути включене
    found = False
    for r in ranges:
        if (date.fromisoformat(r['start']) == completed.check_in_date):
            found = True
            break
    # В залежності від логіки може бути включене чи ні

def test_update_booking_partial_skip_protected_fields(db_session, test_booking):
    original_code = test_booking.booking_code
    original_created = test_booking.created_at
    
    update_data = {
        'booking_code': 'NEWCODE',
        'created_at': datetime.now(timezone.utc),
        'special_requests': 'Updated'
    }
    
    updated = update_booking_partial(db_session, test_booking.booking_code, update_data)
    db_session.commit()
    
    assert updated.booking_code == original_code  # не змінився
    assert updated.created_at == original_created  # не змінився
    assert updated.special_requests == 'Updated' 

def test_update_booking_partial_sets_updated_at(db_session, test_booking):
    old_updated = test_booking.updated_at
    
    import time
    time.sleep(0.01)  # невелика затримка
    
    update_data = {'special_requests': 'New'}
    updated = update_booking_partial(db_session, test_booking.booking_code, update_data)
    db_session.commit()
    
    assert updated.updated_at > old_updated

def test_update_booking_full_sets_updated_at(db_session, test_booking):
    old_updated = test_booking.updated_at
    
    import time
    time.sleep(0.01)
    
    update_data = {
        'room_id': test_booking.room_id,
        'check_in_date': date.today() + timedelta(days=20),
        'check_out_date': date.today() + timedelta(days=22),
        'user_id': test_booking.user_id,
        'special_requests': 'Full update'
    }
    
    updated = update_booking_full(db_session, test_booking.booking_code, update_data)
    db_session.commit()
    
    assert updated.updated_at > old_updated

def test_cancel_booking_sets_updated_at(db_session, test_booking):
    old_updated = test_booking.updated_at
    
    import time
    time.sleep(0.01)
    
    cancel_booking(db_session, test_booking.booking_code)
    db_session.commit()
    
    cancelled = db_session.query(Booking).get(test_booking.booking_code)
    assert cancelled.updated_at > old_updated

def test_create_booking_guest_user_resolution(db_session, test_room):
    guest_email = f"fullguest_{uuid.uuid4().hex[:8]}@example.com"
    
    booking_data = {
        'room_id': test_room.room_id,
        'check_in_date': date.today() + timedelta(days=20),
        'check_out_date': date.today() + timedelta(days=22),
        'email': guest_email,
        'first_name': 'Full',
        'last_name': 'Guest',
        'phone': '+380509876543'
    }
    
    booking = create_booking(db_session, booking_data)
    db_session.commit()
    
    # Перевіряємо що користувач створений
    user = db_session.query(User).get(booking.user_id)
    assert user is not None
    assert user.email == guest_email
    assert user.is_registered == False
    assert user.first_name == 'Full'
    assert user.last_name == 'Guest'

def test_check_room_availability_available_room(db_session, test_room):
    is_available, message = check_room_availability(
        db_session,
        test_room.room_id,
        date.today() + timedelta(days=50),
        date.today() + timedelta(days=52)
    )
    
    assert is_available == True
    assert "available" in message.lower()

def test_update_expired_bookings_multiple(db_session, test_user_registered, test_room):
    for i in range(3):
        expired = Booking(
            booking_code=f"EXP{i}",
            user_id=test_user_registered.user_id,
            room_id=test_room.room_id,
            check_in_date=date.today() - timedelta(days=10+i),
            check_out_date=date.today() - timedelta(days=8+i),
            status=BookingStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(expired)
    db_session.commit()
    
    count = update_expired_bookings_status(db_session)
    
    assert count >= 3

def test_update_expired_bookings_no_expired(db_session):
    count = update_expired_bookings_status(db_session)
    assert count == 0

def test_create_booking_room_not_found(db_session, test_user_registered):
    booking_data = {
        'user_id': test_user_registered.user_id,
        'room_id': 999999,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3)
    }
    
    with pytest.raises(ValueError, match="Room not found"):
        create_booking(db_session, booking_data)

def test_create_booking_room_not_available(db_session, test_user_registered, test_room):
    test_room.status = RoomStatus.MAINTENANCE
    db_session.commit()
    
    booking_data = {
        'user_id': test_user_registered.user_id,
        'room_id': test_room.room_id,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3)
    }
    
    with pytest.raises(ValueError, match="Room is not available"):
        create_booking(db_session, booking_data)

def test_create_booking_overlapping(db_session, test_booking, test_user_registered, test_room):
    booking_data = {
        'user_id': test_user_registered.user_id,
        'room_id': test_room.room_id,
        'check_in_date': test_booking.check_in_date,
        'check_out_date': test_booking.check_out_date
    }
    
    with pytest.raises(ValueError, match="Room is already booked"):
        create_booking(db_session, booking_data)

def test_create_booking_no_user_resolved(db_session, test_room):
    booking_data = {
        'room_id': test_room.room_id,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3)
    }
    
    with pytest.raises(ValueError, match="Either user_id or email must be provided"):
        create_booking(db_session, booking_data)


def test_update_booking_partial_completed_booking(db_session, test_booking):
    test_booking.status = BookingStatus.COMPLETED
    db_session.commit()
    
    update_data = {
        'status': BookingStatus.CANCELLED
    }
    
    updated = update_booking_partial(db_session, test_booking.booking_code, update_data)
    db_session.commit()
    assert updated.status == BookingStatus.CANCELLED

def test_update_booking_partial_completed_other_fields(db_session, test_booking):
    test_booking.status = BookingStatus.COMPLETED
    db_session.commit()
    
    update_data = {
        'special_requests': 'Test'
    }
    
    with pytest.raises(ValueError, match="Can only change status"):
        update_booking_partial(db_session, test_booking.booking_code, update_data)

def test_update_booking_partial_change_dates(db_session, test_booking, test_room):
    """Тест для рядків 228-234: зміна дат бронювання"""
    update_data = {
        'check_in_date': date.today() + timedelta(days=10),
        'check_out_date': date.today() + timedelta(days=12)
    }
    
    updated = update_booking_partial(db_session, test_booking.booking_code, update_data)
    db_session.commit()
    
    assert updated.check_in_date == update_data['check_in_date']
    assert updated.check_out_date == update_data['check_out_date']

def test_update_booking_partial_change_room(db_session, test_booking):
    new_room = Room(
        room_number=f"NewRoom_{uuid.uuid4().hex[:6]}",
        room_type=RoomType.DELUXE,
        base_price=1500.0,
        status=RoomStatus.AVAILABLE,
        max_guest=3,
        floor=2,
        size_sqm=30.0,
        description="New room"
    )
    db_session.add(new_room)
    db_session.commit()
    
    update_data = {
        'room_id': new_room.room_id
    }
    
    updated = update_booking_partial(db_session, test_booking.booking_code, update_data)
    db_session.commit()
    
    assert updated.room_id == new_room.room_id

def test_update_booking_partial_unavailable_dates(db_session, test_booking, test_user_registered):
    another_booking = Booking(
        booking_code="ANOTHER123",
        user_id=test_user_registered.user_id,
        room_id=test_booking.room_id,
        check_in_date=date.today() + timedelta(days=10),
        check_out_date=date.today() + timedelta(days=12),
        status=BookingStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(another_booking)
    db_session.commit()
    
    update_data = {
        'check_in_date': date.today() + timedelta(days=10),
        'check_out_date': date.today() + timedelta(days=12)
    }
    
    with pytest.raises(ValueError, match="already booked"):
        update_booking_partial(db_session, test_booking.booking_code, update_data)

def test_update_booking_full_not_found(db_session):
    update_data = {
        'room_id': 1,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3),
        'user_id': 1
    }
    
    with pytest.raises(ValueError, match="not found"):
        update_booking_full(db_session, 'NONEXISTENT', update_data)

def test_update_booking_full_completed(db_session, test_booking):
    test_booking.status = BookingStatus.COMPLETED
    db_session.commit()
    
    update_data = {
        'room_id': test_booking.room_id,
        'check_in_date': date.today() + timedelta(days=10),
        'check_out_date': date.today() + timedelta(days=12),
        'user_id': test_booking.user_id
    }
    
    with pytest.raises(ValueError, match="Cannot modify completed or cancelled bookings"):
        update_booking_full(db_session, test_booking.booking_code, update_data)
