import uuid

def create_test_user(client, email=None):
    if email is None:
        email = f"{uuid.uuid4().hex[:8]}@example.com"
    new_user = {
        "first_name": "Danylo",
        "last_name": "Ivanenko",
        "email": email,
        "password": "hisPassword456",
        "phone": f"+3806612345{uuid.uuid4().int % 1000:03d}",
        "role": "CUSTOMER"
    }
    response = client.post("/api/v1/users/", json=new_user)
    print(response.status_code, response.get_data(as_text=True))
    assert response.status_code == 201, response.get_data(as_text=True)
    user = response.get_json(force=True)
    assert user["email"] == email
    assert "id" in user
    return user


def test_get_users(client):
    create_test_user(client)
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_single_user(client):
    user = create_test_user(client)
    user_id = user["id"]
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    fetched_user = response.get_json()
    assert fetched_user["id"] == user_id
    assert fetched_user["email"] == user["email"]


def test_create_user(client):
    user = create_test_user(client)
    assert user["first_name"] == "Danylo"
    assert user["role"] == "CUSTOMER"


def test_update_user(client):
    user = create_test_user(client)
    user_id = user["id"]

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
    assert updated_user["id"] == user_id


def test_delete_user(client):
    user = create_test_user(client)
    user_id = user["id"]

    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404
