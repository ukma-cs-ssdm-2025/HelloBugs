import json
from datetime import datetime, timedelta
import uuid
from tests.test_rooms import create_test_room
from tests.test_users import create_test_user

def create_test_booking(client):
    room = create_test_room(client)
    room_id = room["id"]

    user = create_test_user(client)
    user_id = user["id"]

    check_in_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    check_out_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")

    booking_code = f"BK-{uuid.uuid4().hex[:6]}"
    new_booking = {
        "user_id": user_id,
        "room_id": room_id,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "special_requests": "Телевізор, два крєсла",
        "status": "ACTIVE"
    }

    response = client.post(
        "/api/v1/bookings/",
        data=json.dumps(new_booking),
        content_type="application/json"
    )
    booking = response.get_json(force=True)
    assert response.status_code in (200, 201), f"Не вдалося створити бронювання: {response.data}"
    return booking


def test_get_bookings(client):
    create_test_booking(client)
    response = client.get("/api/v1/bookings/")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if len(data) > 0:
        first_booking = data[0]
        for key in ["booking_code", "status"]:
            assert key in first_booking


def test_get_single_booking(client):
    booking = create_test_booking(client)
    booking_code = booking["booking_code"]
    response = client.get(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 200
    single_booking = response.get_json()
    assert single_booking["booking_code"] == booking_code


def test_create_booking(client):
    booking = create_test_booking(client)
    assert booking["special_requests"] == "Телевізор, два крєсла"


def test_update_booking(client):
    booking = create_test_booking(client)
    booking_code = booking["booking_code"]

    update_data = {
        "user_id": booking["user_id"],
        "room_id": booking["room_id"],
        "check_in_date": booking["check_in_date"],
        "check_out_date": booking["check_out_date"],
        "special_requests": "Сніданок у номер",
        "status": booking["status"]
    }

    response = client.put(f"/api/v1/bookings/{booking_code}", json=update_data)
    assert response.status_code == 200
    updated_booking = response.get_json()
    assert updated_booking["special_requests"] == "Сніданок у номер"


def test_cancel_booking(client):
    booking = create_test_booking(client)
    booking_code = booking["booking_code"]

    response = client.delete(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 200
    cancelled_booking = response.get_json()
    assert cancelled_booking["status"] == "CANCELLED"