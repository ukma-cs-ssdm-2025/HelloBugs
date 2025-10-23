import uuid

def create_test_user(client, email=None, **kwargs):
    if email is None:
        email = f"{uuid.uuid4().hex[:8]}@gmail.com"

    new_user = {
        "first_name": "Danylo",
        "last_name": "Ivanenko",
        "email": email,
        "password": "hisPassword456",
        "phone": f"+3806613345{uuid.uuid4().int % 1000:03d}",
        "role": "GUEST"
    }
    new_user.update(kwargs)

    response = client.post("/api/v1/users/", json=new_user)

    assert response.status_code == 201
    user = response.get_json(force=True)
    assert user["email"] == email
    return user


def test_get_users(client):
    """Тест отримання списку користувачів"""
    create_test_user(client)
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_single_user(client):
    user = create_test_user(client)
    user_id = user.get("id") or user.get("user_id")
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    fetched_user = response.get_json()
    fetched_id = fetched_user.get("id") or fetched_user.get("user_id")
    assert fetched_id == user_id
    assert fetched_user["email"] == user["email"]


def test_create_user(client):
    user = create_test_user(client)
    assert user["first_name"] == "Danylo"
    assert user["role"] == "GUEST"


def test_update_user(client):
    user = create_test_user(client)
    user_id = user.get("id") or user.get("user_id")

    update_data = {
        "first_name": "Daniil",
        "last_name": user["last_name"],
        "email": user["email"],
        "password": "hisNewPassword456",
        "phone": user["phone"],
        "role": user["role"]
    }

    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200

    updated_user = response.get_json()
    assert updated_user["first_name"] == "Daniil"

    updated_id = updated_user.get("id") or updated_user.get("user_id")
    assert updated_id == user_id


def test_delete_user(client):
    user = create_test_user(client)
    user_id = user.get("id") or user.get("user_id")

    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404


def test_create_user_duplicate_email(client):
    email = f"duplicate-{uuid.uuid4().hex[:8]}@test.com"
    create_test_user(client, email=email)

    response = client.post("/api/v1/users/", json={
        "first_name": "Another",
        "last_name": "User",
        "email": email,
        "password": "password123",
        "phone": "+380661234567",
        "role": "GUEST"
    })

    assert response.status_code == 400


def test_get_nonexistent_user(client):
    response = client.get("/api/v1/users/999999")
    assert response.status_code == 404


def test_create_user_invalid_email(client):
    response = client.post("/api/v1/users/", json={
        "first_name": "Test",
        "last_name": "User",
        "email": "not-an-email",
        "password": "password123",
        "phone": "+380661234567",
        "role": "GUEST"
    })

    assert response.status_code in (400, 422)