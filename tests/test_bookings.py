import json
from datetime import datetime, timedelta


def test_get_bookings(client):
    response = client.get("/api/v1/bookings/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    if len(data) > 0:
        booking = data[0]
        assert "booking_code" in booking
        assert "guest_email" in booking
        assert "status" in booking


def test_get_single_booking(client):
    response = client.get("/api/v1/bookings/")
    bookings = json.loads(response.data)
    if not bookings:
        test_create_booking(client)
        response = client.get("/api/v1/bookings/")
        bookings = json.loads(response.data)
    booking_code = bookings[0]["booking_code"]
    response = client.get(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.data}"
    booking = json.loads(response.data)
    assert booking["booking_code"] == booking_code
    assert "guest_email" in booking
    assert "status" in booking


def test_create_booking(client):
    from tests.test_rooms import test_create_room
    room = test_create_room(client)
    assert room is not None, "Не вдалося створити тестову кімнату"
    room_id = room["id"]
    timestamp = int(datetime.now().timestamp())
    user_email = f"booking_test_{timestamp}@example.com"
    new_user = {
        "first_name": "Бронювач",
        "last_name": "Тестовий",
        "email": user_email,
        "password": "testpassword123",
        "phone": f"+38050{timestamp % 10000000:07d}",
        "role": "CUSTOMER"
    }
    response = client.post(
        "/api/v1/users/",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    if response.status_code != 201:
        response = client.get("/api/v1/users/")
        users = json.loads(response.data)
        assert len(users) > 0, "Не знайдено жодного користувача і не вдалося створити нового"
        user_id = users[0]["id"]
    else:
        user = json.loads(response.data)
        user_id = user["id"]
    days_offset = timestamp % 1000
    base_date = datetime.now() + timedelta(days=365)
    check_in = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
    check_out = (base_date + timedelta(days=days_offset + 3)).strftime("%Y-%m-%d")
    new_booking = {
        "user_id": user_id,
        "guest_email": f"booking_{timestamp}@example.com",
        "guest_first_name": "Тестовий",
        "guest_last_name": "Гість",
        "guest_phone": f"+38050{timestamp % 10000000:07d}",
        "room_id": room_id,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "number_of_guests": 2,
        "special_requests": "Тестове бронювання"
    }
    response = client.post(
        "/api/v1/bookings/",
        data=json.dumps(new_booking),
        content_type="application/json"
    )
    assert response.status_code in (201, 200), (
        f"Очікувався код статусу 201 або 200, отримано {response.status_code}: {response.data}"
    )
    booking = json.loads(response.data)
    required_fields = ["booking_code", "check_in_date", "check_out_date", "guest_email"]
    for field in required_fields:
        assert field in booking, f"У відповіді відсутнє обов'язкове поле '{field}'. Отримано: {booking.keys()}"
    assert booking["guest_email"] == new_booking["guest_email"], "Email не співпадає"
    assert booking["check_in_date"] == check_in, "Дата заїзду не співпадає"
    assert booking["check_out_date"] == check_out, "Дата виїзду не співпадає"
    return booking


def test_update_booking(client):
    booking = test_create_booking(client)
    booking_code = booking["booking_code"]
    response = client.get(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 200, f"Не вдалося отримати бронювання: {response.data}"
    current_booking = json.loads(response.data)
    timestamp = int(datetime.now().timestamp())
    update_data = {
        "guest_email": f"updated_{timestamp}@example.com",
        "guest_first_name": "Оновлений",
        "guest_last_name": "Користувач",
        "guest_phone": f"+38050{timestamp % 10000000:07d}",
        "special_requests": "Оновлені особливі побажання",
        "number_of_guests": 3
    }
    for field in ["user_id", "room_id", "check_in_date", "check_out_date"]:
        if field in current_booking:
            update_data[field] = current_booking[field]
    check_in = datetime.strptime(update_data["check_in_date"], "%Y-%m-%d")
    check_out = datetime.strptime(update_data["check_out_date"], "%Y-%m-%d")
    update_data["check_in_date"] = (check_in + timedelta(days=10)).strftime("%Y-%m-%d")
    update_data["check_out_date"] = (check_out + timedelta(days=10)).strftime("%Y-%m-%d")
    
    response = client.put(
        f"/api/v1/bookings/{booking_code}",
        data=json.dumps(update_data),
        content_type="application/json"
    )
    
    assert response.status_code == 200, (
        f"Очікувався код статусу 200, отримано {response.status_code}: {response.data}"
    )
    updated_booking = json.loads(response.data)
    assert updated_booking["guest_email"] == update_data["guest_email"], "Email не оновився"
    assert updated_booking["guest_first_name"] == "Оновлений", "Ім'я не оновилося"
    assert updated_booking["guest_last_name"] == "Користувач", "Прізвище не оновилося"
    assert updated_booking["special_requests"] == "Оновлені особливі побажання", "Особливі побажання не оновилися"
    assert updated_booking["check_in_date"] == update_data["check_in_date"], "Дата заїзду не оновилася"
    assert updated_booking["check_out_date"] == update_data["check_out_date"], "Дата виїзду не оновилася"
    return updated_booking


def test_cancel_booking(client):
    booking = test_create_booking(client)
    booking_code = booking["booking_code"]
    response = client.get(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 200, f"Не вдалося отримати бронювання: {response.data}"
    booking_data = json.loads(response.data)
    assert booking_data["status"] != "CANCELLED", "Бронювання вже скасоване"
    response = client.delete(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 204, f"Не вдалося скасувати бронювання: {response.status_code} - {response.data}"
    response = client.get(f"/api/v1/bookings/{booking_code}")
    assert response.status_code == 200, f"Не вдалося отримати оновлене бронювання: {response.status_code}"
    cancelled_booking = json.loads(response.data)
    assert cancelled_booking["status"] == "CANCELLED", f"Очікувався статус 'CANCELLED', отримано '{cancelled_booking['status']}'"
