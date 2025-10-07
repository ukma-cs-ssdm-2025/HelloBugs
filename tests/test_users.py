import json

def test_get_users(client):
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_single_user(client):
    response = client.get("/api/v1/users/")
    users = json.loads(response.data)
    user_id = users[0]["id"] 
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    user = json.loads(response.data)
    assert user["id"] == user_id


def test_create_user(client):
    new_user = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password": "testpassword123",
        "phone": "+380501234567",
        "role": "CUSTOMER"
    }
    response = client.post(
        "/api/v1/users/",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    assert response.status_code == 201
    user = json.loads(response.data)
    assert user["email"] == "test@example.com"
    assert user["first_name"] == "Test"
    assert "id" in user


def test_update_user(client):
    response = client.get("/api/v1/users/")
    users = json.loads(response.data)
    user_id = users[0]["id"]
    update_data = {
        "first_name": "Updated",
        "last_name": users[0]["last_name"],
        "email": users[0]["email"],
        "password": "newpassword123",
        "phone": users[0]["phone"],
        "role": users[0]["role"]
    }
    response = client.put(
        f"/api/v1/users/{user_id}",
        data=json.dumps(update_data),
        content_type="application/json"
    )
    assert response.status_code == 200
    user = json.loads(response.data)
    assert user["first_name"] == "Updated"


def test_delete_user(client):
    new_user = {
        "first_name": "ToDelete",
        "last_name": "User",
        "email": "todelete@example.com",
        "password": "testpassword123",
        "phone": "+380501234567",
        "role": "CUSTOMER"
    }
    response = client.post(
        "/api/v1/users/",
        data=json.dumps(new_user),
        content_type="application/json"
    )
    user = json.loads(response.data)
    user_id = user["id"]
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404
