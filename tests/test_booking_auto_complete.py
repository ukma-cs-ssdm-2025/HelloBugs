import pytest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
import secrets
from src.api.services.booking_service import (
    create_booking,
    get_all_bookings,
    update_expired_bookings_status
)
from src.api.models.booking_model import BookingStatus
from src.api.models.user_model import User, UserRole
from src.api.models.room_model import Room, RoomType, RoomStatus


@pytest.fixture
def seed_user(db_session):
    user = User(
        first_name="Test",
        last_name="User",
        email="test_auto_complete@example.com",
        phone="+380501234567",
        role=UserRole.GUEST,
        is_registered=True,
        password=generate_password_hash(secrets.token_urlsafe(16))
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def seed_room(db_session):
    room = Room(
        room_number="101",
        room_type=RoomType.STANDARD,
        max_guest=2,
        base_price=100.0,
        status=RoomStatus.AVAILABLE,
        floor=1,
        description="Test room for auto-complete"
    )
    db_session.add(room)
    db_session.commit()
    return room


def test_expired_booking_auto_completes(db_session, seed_user, seed_room):
    """Тест автоматичного оновлення статусу бронювання на COMPLETED"""
    from src.api.models.booking_model import Booking
    from datetime import datetime, timezone
    
    # Створюємо бронювання яке вже завершилось (check_out_date в минулому)
    # Створюємо напряму через модель, щоб обійти валідацію дат
    past_booking = Booking(
        booking_code="BK_TEST_PAST_001",
        user_id=seed_user.user_id,
        room_id=seed_room.room_id,
        check_in_date=date.today() - timedelta(days=5),
        check_out_date=date.today() - timedelta(days=2),
        special_requests='Past booking',
        status=BookingStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(past_booking)
    db_session.commit()
    
    # Перевіряємо що статус ACTIVE
    assert past_booking.status == BookingStatus.ACTIVE
    
    # Викликаємо функцію оновлення
    count = update_expired_bookings_status(db_session)
    
    # Перевіряємо що оновилось 1 бронювання
    assert count == 1
    
    # Перевіряємо що статус змінився на COMPLETED
    db_session.refresh(past_booking)
    assert past_booking.status == BookingStatus.COMPLETED


def test_active_booking_not_auto_completed(db_session, seed_user, seed_room):
    """Тест що активні бронювання не оновлюються"""
    # Створюємо майбутнє бронювання
    future_booking = create_booking(db_session, {
        'user_id': seed_user.user_id,
        'room_id': seed_room.room_id,
        'check_in_date': date.today() + timedelta(days=1),
        'check_out_date': date.today() + timedelta(days=3),
        'special_requests': 'Future booking'
    })
    
    # Викликаємо функцію оновлення
    count = update_expired_bookings_status(db_session)
    
    # Перевіряємо що нічого не оновилось
    assert count == 0
    
    # Перевіряємо що статус залишився ACTIVE
    db_session.refresh(future_booking)
    assert future_booking.status == BookingStatus.ACTIVE


def test_get_all_bookings_auto_updates(db_session, seed_user, seed_room):
    """Тест що get_all_bookings автоматично оновлює статуси"""
    from src.api.models.booking_model import Booking
    from datetime import datetime, timezone
    
    # Створюємо застаріле бронювання напряму через модель
    old_booking = Booking(
        booking_code="BK_TEST_OLD_001",
        user_id=seed_user.user_id,
        room_id=seed_room.room_id,
        check_in_date=date.today() - timedelta(days=10),
        check_out_date=date.today() - timedelta(days=8),
        special_requests='Old booking',
        status=BookingStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(old_booking)
    db_session.commit()
    
    # Отримуємо всі бронювання (має автоматично оновити статус)
    bookings = get_all_bookings(db_session)
    
    # Перевіряємо що бронювання має статус COMPLETED
    assert len(bookings) == 1
    assert bookings[0].status == BookingStatus.COMPLETED
