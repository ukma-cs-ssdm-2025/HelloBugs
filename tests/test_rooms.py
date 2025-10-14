import uuid

def create_test_room(client, room_number=None):
    if room_number is None:
        room_number = f"{uuid.uuid4().int % 1000:03d}"
    new_room = {
        "room_number": room_number,
        "room_type": "STANDARD",
        "max_guest": 2,
        "base_price": 1500.00,
        "status": "AVAILABLE",
        "floor": 2
    }
    response = client.post("/api/v1/rooms/", json=new_room)
    print(response.status_code, response.get_data(as_text=True))
    assert response.status_code == 201, response.get_data(as_text=True)
    room = response.get_json(force=True)
    assert room["room_number"] == room_number
    assert "id" in room
    return room

def test_get_rooms(client):
    create_test_room(client)
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if len(data) > 0:
        room = data[0]
        for field in ["id", "room_number", "room_type", "base_price"]:
            assert field in room


def test_get_single_room(client):
    room = create_test_room(client)
    room_id = room["id"]
    response = client.get(f"/api/v1/rooms/{room_id}")
    assert response.status_code == 200
    fetched_room = response.get_json()
    assert fetched_room["id"] == room_id
    assert "room_number" in fetched_room
    assert "room_type" in fetched_room


def test_create_room(client):
    room = create_test_room(client)
    assert room["room_type"] == "STANDARD"
    assert room["status"] == "AVAILABLE"
    assert "id" in room


def test_update_room(client):
    room = create_test_room(client)
    room_id = room["id"]

    update_data = {
        "room_number": room["room_number"],
        "room_type": room["room_type"],
        "max_guest": room["max_guest"],
        "base_price": 1700.00,
        "floor": room["floor"],
        "status": "MAINTENANCE"
    }

    response = client.put(f"/api/v1/rooms/{room_id}", json=update_data)
    assert response.status_code == 200
    updated_room = response.get_json()
    assert float(updated_room["base_price"]) == 1700.00
    assert updated_room["status"] == "MAINTENANCE"

def test_partial_update_room(client):
    room = create_test_room(client)
    room_id = room["id"]

    patch_data = {
        "base_price": 2500.00,
        "status": "MAINTENANCE"
    }
    response = client.patch(f"/api/v1/rooms/{room_id}", json=patch_data)
    assert response.status_code == 200
    updated_room = response.get_json()
    assert float(updated_room["base_price"]) == 2500.00
    assert updated_room["status"] == "MAINTENANCE"


def test_delete_room(client):
    room = create_test_room(client)
    room_id = room["id"]

    response = client.delete(f"/api/v1/rooms/{room_id}")
    assert response.status_code in (200, 204)

    response = client.get(f"/api/v1/rooms/{room_id}")
    assert response.status_code == 404