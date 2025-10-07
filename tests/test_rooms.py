import json
import time
import random
import string


def test_get_rooms(client):
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    if len(data) > 0:
        room = data[0]
        assert "id" in room
        assert "room_number" in room
        assert "room_type" in room
        assert "base_price" in room


def test_get_single_room(client):
    response = client.get("/api/v1/rooms/")
    rooms = json.loads(response.data)
    if not rooms:
        test_create_room(client)
        response = client.get("/api/v1/rooms/")
        rooms = json.loads(response.data)
    room_id = rooms[0]["id"]
    response = client.get(f"/api/v1/rooms/{room_id}")
    assert response.status_code == 200
    room = json.loads(response.data)
    assert room["id"] == room_id
    assert "room_number" in room
    assert "room_type" in room


def test_create_room(client):
    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    room_number = f"T{timestamp % 10000}{random_str}"
    new_room = {
        "room_number": room_number,
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 150.00,
        "floor": 9,
        "size_sqm": 30.0,
        "description": f"Зручний стандартний номер {room_number}",
        "main_photo_url": "https://example.com/room.jpg",
        "has_balcony": True,
        "has_minibar": True,
        "is_smoking_allowed": False,
        "status": "AVAILABLE"
    }
    response = client.post(
        "/api/v1/rooms/",
        data=json.dumps(new_room),
        content_type="application/json"
    )
    if response.status_code == 422:
        new_room = {
            "room_number": room_number,
            "room_type": "STANDARD",
            "max_guest": 2,
            "base_price": 150.00,
            "status": "AVAILABLE"
        }
        response = client.post(
            "/api/v1/rooms/",
            data=json.dumps(new_room),
            content_type="application/json"
        )
    assert response.status_code in (201, 200), f"Expected status code 201 or 200, got {response.status_code}: {response.data}"
    if response.status_code in (201, 200):
        room = json.loads(response.data)
        assert "id" in room
        assert room["room_number"] == room_number
        assert room["room_type"] == "STANDARD"
        return room
    response = client.get("/api/v1/rooms/")
    rooms = json.loads(response.data)
    if rooms:
        return rooms[0] 
    raise AssertionError(f"Не вдалося створити кімнату: {response.status_code} - {response.data}")



def test_update_room(client):
    response = client.get("/api/v1/rooms/")
    rooms = json.loads(response.data)
    if not rooms:
        test_create_room(client)
        response = client.get("/api/v1/rooms/")
        rooms = json.loads(response.data)
    room_id = rooms[0]["id"]
    response = client.get(f"/api/v1/rooms/{room_id}")
    room = json.loads(response.data)
    update_data = {
        "room_number": room["room_number"],
        "room_type": "DELUXE",
        "max_guest": room.get("max_guest", 2),
        "base_price": 200.00,
        "floor": room.get("floor", 1),
        "size_sqm": room.get("size_sqm", 30.0),
        "description": room.get("description", "Оновлений опис номера"),
        "main_photo_url": room.get("main_photo_url", "https://example.com/room.jpg"),
        "status": room.get("status", "AVAILABLE")
    }
    for field in ["floor", "has_balcony", "has_minibar", "is_smoking_allowed"]:
        if field in room:
            update_data[field] = room[field]
    
    response = client.put(
        f"/api/v1/rooms/{room_id}",
        data=json.dumps(update_data),
        content_type="application/json"
    )
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.data}"
    updated_room = json.loads(response.data)
    assert updated_room["room_type"] == "DELUXE"
    assert float(updated_room["base_price"]) == 200.00


def test_partial_update_room(client):
    response = client.get("/api/v1/rooms/")
    rooms = json.loads(response.data)
    if not rooms:
        test_create_room(client)
        response = client.get("/api/v1/rooms/")
        rooms = json.loads(response.data)
    room_id = rooms[0]["id"]
    patch_data = {
        "base_price": 250.00,
        "status": "MAINTENANCE"
    }
    response = client.patch(
        f"/api/v1/rooms/{room_id}",
        data=json.dumps(patch_data),
        content_type="application/json"
    )
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}: {response.data}"
    room = json.loads(response.data)
    assert float(room["base_price"]) == 250.00
    assert room["status"] == "MAINTENANCE"


def test_delete_room(client):
    new_room = {
        "room_number": "DELETE_ME",
        "room_type": "STANDARD",
        "max_guest": 1,
        "base_price": 50.00,
        "status": "AVAILABLE"
    }
    response = client.post(
        "/api/v1/rooms/",
        data=json.dumps(new_room),
        content_type="application/json"
    )
    if response.status_code != 201:
        response = client.get("/api/v1/rooms/")
        rooms = json.loads(response.data)
        assert len(rooms) > 0, "No rooms found and cannot create a new one"
        room_id = rooms[0]["id"]
    else:
        room = json.loads(response.data)
        room_id = room["id"]
    response = client.delete(f"/api/v1/rooms/{room_id}")
    assert response.status_code in (200, 204), f"Expected status code 200 or 204, got {response.status_code}: {response.data}"
    response = client.get(f"/api/v1/rooms/{room_id}")
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"
