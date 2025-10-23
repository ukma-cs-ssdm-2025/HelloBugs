# import uuid
#
# def create_test_room(client, room_number=None, **kwargs):
#     if room_number is None:
#         room_number = f"{uuid.uuid4().int % 1000:03d}"
#
#     new_room = {
#         "room_number": room_number,
#         "room_type": "STANDARD",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     }
#     new_room.update(kwargs)
#
#     response = client.post("/api/v1/rooms/", json=new_room)
#     assert response.status_code == 201, response.get_data(as_text=True)
#     room = response.get_json()
#     assert "id" in room
#     return room
#
#
# def test_get_rooms(client):
#     create_test_room(client)
#     response = client.get("/api/v1/rooms/")
#     assert response.status_code == 200
#     data = response.get_json()
#     assert isinstance(data, list)
#     if len(data) > 0:
#         room = data[0]
#         for field in ["id", "room_number", "room_type", "base_price"]:
#             assert field in room
#
#
# def test_get_single_room(client):
#     room = create_test_room(client)
#     room_id = room["id"]
#     response = client.get(f"/api/v1/rooms/{room_id}")
#     assert response.status_code == 200
#     fetched_room = response.get_json()
#     assert fetched_room["id"] == room_id
#     assert "room_number" in fetched_room
#     assert "room_type" in fetched_room
#
#
# def test_create_room(client):
#     room = create_test_room(client)
#     assert room["room_type"] == "STANDARD"
#     assert room["status"] == "AVAILABLE"
#     assert "id" in room
#
#
# def test_update_room(client):
#     room = create_test_room(client)
#     room_id = room["id"]
#
#     update_data = {
#         "room_number": room["room_number"],
#         "room_type": room["room_type"],
#         "max_guest": room["max_guest"],
#         "base_price": 1700.00,
#         "floor": room["floor"],
#         "status": "MAINTENANCE"
#     }
#
#     response = client.put(f"/api/v1/rooms/{room_id}", json=update_data)
#     assert response.status_code == 200
#     updated_room = response.get_json()
#     assert float(updated_room["base_price"]) == 1700.00
#     assert updated_room["status"] == "MAINTENANCE"
#
#
# def test_partial_update_room(client):
#     room = create_test_room(client)
#     room_id = room["id"]
#
#     patch_data = {
#         "base_price": 2500.00,
#         "status": "MAINTENANCE"
#     }
#     response = client.patch(f"/api/v1/rooms/{room_id}", json=patch_data)
#     assert response.status_code == 200
#     updated_room = response.get_json()
#     assert float(updated_room["base_price"]) == 2500.00
#     assert updated_room["status"] == "MAINTENANCE"
#
#
# def test_delete_room(client):
#     room = create_test_room(client)
#     room_id = room["id"]
#
#     response = client.delete(f"/api/v1/rooms/{room_id}")
#     assert response.status_code in (200, 204)
#
#     response = client.get(f"/api/v1/rooms/{room_id}")
#     assert response.status_code == 404
#
#
# def test_create_room_duplicate_number(client):
#     room_number = "DUP-001"
#     create_test_room(client, room_number=room_number)
#
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": room_number,
#         "room_type": "DELUXE",
#         "max_guest": 3,
#         "base_price": 2000.00,
#         "status": "AVAILABLE",
#         "floor": 3
#     })
#
#     assert response.status_code == 409
#     data = response.get_json()
#     assert "already exists" in data.get("message", "").lower()
#
#
# def test_create_room_invalid_type(client):
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": "INV-001",
#         "room_type": "SUPER_LUXURY",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     })
#
#     assert response.status_code in (400, 422)
#
#
# def test_create_room_invalid_status(client):
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": "INV-002",
#         "room_type": "STANDARD",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "DESTROYED",  # Невалідний статус
#         "floor": 2
#     })
#
#     assert response.status_code in (400, 422)
#
#
# def test_create_room_missing_required_fields(client):
#     response = client.post("/api/v1/rooms/", json={
#         "room_type": "STANDARD",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     })
#     assert response.status_code in (400, 422)
#
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": "MIS-001",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     })
#     assert response.status_code in (400, 422)
#
#
# def test_create_room_boundary_max_guest(client):
#     room1 = create_test_room(client, room_number="B-001", max_guest=1)
#     assert room1["max_guest"] == 1
#
#     room2 = create_test_room(client, room_number="B-002", max_guest=10)
#     assert room2["max_guest"] == 10
#
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": "B-003",
#         "room_type": "STANDARD",
#         "max_guest": 0,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     })
#
#     assert response.status_code in (400, 422)
#
#
# def test_create_room_boundary_floor(client):
#     room1 = create_test_room(client, room_number="F-001", floor=1)
#     assert room1["floor"] == 1
#
#     room2 = create_test_room(client, room_number="F-002", floor=50)
#     assert room2["floor"] == 50
#
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": "FLOOR-003",
#         "room_type": "STANDARD",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 51
#     })
#     assert response.status_code in (400, 422)
#
#
# def test_create_room_negative_price(client):
#     response = client.post("/api/v1/rooms/", json={
#         "room_number": "NEG-001",
#         "room_type": "STANDARD",
#         "max_guest": 2,
#         "base_price": -100.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     })
#
#     assert response.status_code in (400, 422)
#
#
# def test_update_room_change_to_existing_number(client):
#     room1 = create_test_room(client, room_number="EXIST-001")
#     room2 = create_test_room(client, room_number="EXIST-002")
#
#     response = client.patch(f"/api/v1/rooms/{room2['id']}", json={
#         "room_number": "EXIST-001"
#     })
#
#     assert response.status_code == 409
#
#
# def test_get_nonexistent_room(client):
#     response = client.get("/api/v1/rooms/999999")
#     assert response.status_code == 404
#
#
# def test_update_nonexistent_room(client):
#     response = client.put("/api/v1/rooms/999999", json={
#         "room_number": "GHOST",
#         "room_type": "STANDARD",
#         "max_guest": 2,
#         "base_price": 1500.00,
#         "status": "AVAILABLE",
#         "floor": 2
#     })
#     assert response.status_code == 404
#
#
# def test_delete_nonexistent_room(client):
#     response = client.delete("/api/v1/rooms/999999")
#     assert response.status_code == 404
#
#
# def test_room_status_transitions(client):
#     room = create_test_room(client)
#
#     # AVAILABLE -> OCCUPIED
#     response = client.patch(f"/api/v1/rooms/{room['id']}", json={
#         "status": "OCCUPIED"
#     })
#     assert response.status_code == 200
#     assert response.get_json()["status"] == "OCCUPIED"
#
#     # OCCUPIED -> MAINTENANCE
#     response = client.patch(f"/api/v1/rooms/{room['id']}", json={
#         "status": "MAINTENANCE"
#     })
#     assert response.status_code == 200
#     assert response.get_json()["status"] == "MAINTENANCE"
#
#     # MAINTENANCE -> AVAILABLE
#     response = client.patch(f"/api/v1/rooms/{room['id']}", json={
#         "status": "AVAILABLE"
#     })
#     assert response.status_code == 200
#     assert response.get_json()["status"] == "AVAILABLE"
#
#
# def test_create_all_room_types(client):
#     room_types = ["ECONOMY", "STANDARD", "DELUXE"]
#
#     for idx, room_type in enumerate(room_types):
#         room = create_test_room(
#             client,
#             room_number=f"TYPE-{idx:03d}",
#             room_type=room_type
#         )
#         assert room["room_type"] == room_type