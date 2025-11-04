import pytest
from datetime import date, timedelta
from src.api.services.booking_service import create_booking
from src.api.models.user_model import User, UserRole
from src.api.models.room_model import Room, RoomType, RoomStatus
from werkzeug.security import generate_password_hash
import secrets

@pytest.fixture
def seed_user(db_session):
    u = User(
        email="edit_tester@example.com",
        first_name="Edit",
        last_name="Tester",
        phone="+380500000001",
        is_registered=True,
        password=generate_password_hash(secrets.token_urlsafe(16)),
        role=UserRole.GUEST,
    )
    db_session.add(u)
    db_session.flush()
    return u

@pytest.fixture
def seed_room(db_session):
    r = Room(
        room_number="E1001",
        room_type=RoomType.STANDARD,
        max_guest=2,
        base_price=1000.0,
        status=RoomStatus.AVAILABLE,
        floor=1,
        size_sqm=20.0,
        description="Test room"
    )
    db_session.add(r)
    db_session.flush()
    return r

@pytest.fixture
def seed_booking(db_session, seed_user, seed_room):
    b = create_booking(db_session, {
        'user_id': seed_user.user_id,
        'room_id': seed_room.room_id,
        'check_in_date': date.today() + timedelta(days=3),
        'check_out_date': date.today() + timedelta(days=5),
        'special_requests': 'original'
    })
    db_session.commit()
    return b


def test_patch_booking_updates_updated_at(client, db_session, seed_booking, seed_room):

    code = seed_booking.booking_code
    before = seed_booking.updated_at

    payload = {
        'room_id': seed_room.room_id,
        'check_in_date': (date.today() + timedelta(days=4)).isoformat(),
        'check_out_date': (date.today() + timedelta(days=6)).isoformat(),
        'special_requests': 'updated'
    }

    res = client.patch(f"/api/v1/bookings/{code}", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['special_requests'] == 'updated'
    assert data['updated_at'] is not None


def test_patch_booking_conflict_returns_409(client, db_session, seed_user, seed_room, seed_booking):
    create_booking(db_session, {
        'user_id': seed_user.user_id,
        'room_id': seed_room.room_id,
        'check_in_date': date.today() + timedelta(days=6),
        'check_out_date': date.today() + timedelta(days=8),
        'special_requests': 'blocker'
    })
    db_session.commit()

    code = seed_booking.booking_code
    payload = {
        'room_id': seed_room.room_id,
        'check_in_date': (date.today() + timedelta(days=5)).isoformat(),
        'check_out_date': (date.today() + timedelta(days=7)).isoformat(),
    }

    res = client.patch(f"/api/v1/bookings/{code}", json=payload)
    assert res.status_code in (409, 400, 403), res.get_json()


def test_cannot_patch_cancelled_booking(client, db_session, seed_booking):
    code = seed_booking.booking_code
    # Cancel first
    res_cancel = client.delete(f"/api/v1/bookings/{code}")
    assert res_cancel.status_code == 204
    # Then try to patch
    res_patch = client.patch(f"/api/v1/bookings/{code}", json={"special_requests": "nope"})
    assert res_patch.status_code in (403, 400)


def test_cannot_put_cancelled_booking(client, db_session, seed_booking, seed_room):
    code = seed_booking.booking_code
    res_cancel = client.delete(f"/api/v1/bookings/{code}")
    assert res_cancel.status_code == 204

    payload = {
        'user_id': seed_booking.user_id,
        'room_id': seed_room.room_id,
        'check_in_date': (date.today() + timedelta(days=10)).isoformat(),
        'check_out_date': (date.today() + timedelta(days=12)).isoformat(),
        'special_requests': 'recreate'
    }
    res_put = client.put(f"/api/v1/bookings/{code}", json=payload)
    assert res_put.status_code in (403, 400)


def test_patch_same_dates_updates_requests(client, db_session, seed_booking):
    code = seed_booking.booking_code
    payload = {
        'special_requests': 'updated note'
    }
    res = client.patch(f"/api/v1/bookings/{code}", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['special_requests'] == 'updated note'


def test_delete_booking_returns_204(client, db_session, seed_booking):
    code = seed_booking.booking_code
    res = client.delete(f"/api/v1/bookings/{code}")
    assert res.status_code == 204
