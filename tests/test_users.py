import pytest
from datetime import datetime
from src.api.services.user_service import (create_user, get_all_users, get_user_by_id,
                                           get_user_by_email, update_user_partial, delete_user)
from src.api.models.user_model import User, UserRole
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

@pytest.fixture
def test_user_dict():
    return {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Registered",
        "last_name": "User",
        "phone": "+380674567892",
        "password": "testpassword123",
        "role": "GUEST"
    }

@pytest.fixture
def existing_user(db_session):
    user = User(
        email=f"existing_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Existing",
        last_name="User",
        phone="+380674567892",
        is_registered=True,
        password=generate_password_hash("testpassword123"),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_create_user_success(db_session, test_user_dict):
    user = create_user(db_session, test_user_dict)
    db_session.commit()

    assert user is not None
    assert user.user_id is not None
    assert user.email == test_user_dict["email"]
    assert user.first_name == test_user_dict["first_name"]
    assert user.last_name == test_user_dict["last_name"]
    assert user.role == UserRole.GUEST
    assert user.is_registered == True
    assert check_password_hash(user.password, "testpassword123")

def test_create_user_duplicate_email(db_session, existing_user):
    duplicate_data = {
        "email": existing_user.email,
        "first_name": "Second",
        "last_name": "User",
        "phone": "+380502222222",
        "password": "password456",
        "role": "GUEST"
    }

    with pytest.raises(ValueError, match="User with this email already exists"):
        create_user(db_session, duplicate_data)

def test_get_all_users(db_session, existing_user):
    users = get_all_users(db_session)
    assert isinstance(users, list)
    assert len(users) > 0
    assert any(user.user_id == existing_user.user_id for user in users)

def test_get_user_by_id(db_session, existing_user):
    found_user = get_user_by_id(db_session, existing_user.user_id)
    assert found_user is not None
    assert found_user.user_id == existing_user.user_id
    assert found_user.email == existing_user.email

def test_get_user_by_email(db_session, existing_user):
    found_user = get_user_by_email(db_session, existing_user.email)
    assert found_user is not None
    assert found_user.email == existing_user.email
    assert found_user.user_id == existing_user.user_id

def test_update_user_partial(db_session, existing_user):
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "phone": "+380506667788"
    }

    updated_user = update_user_partial(db_session, existing_user.user_id, update_data)
    db_session.commit()

    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.phone == "+380506667788"
    assert updated_user.email == existing_user.email

def test_update_user_password(db_session, existing_user):
    update_data = {
        "password": "newpassword123"
    }

    updated_user = update_user_partial(db_session, existing_user.user_id, update_data)
    db_session.commit()

    assert check_password_hash(updated_user.password, "newpassword123")

def test_delete_user(db_session, existing_user):
    result = delete_user(db_session, existing_user.user_id)
    db_session.commit()

    assert result is True

    deleted_user = get_user_by_id(db_session, existing_user.user_id)
    assert deleted_user is None

def test_get_user_by_id_not_found(db_session):
    found_user = get_user_by_id(db_session, 999999)
    assert found_user is None

def test_get_user_by_email_not_found(db_session):
    found_user = get_user_by_email(db_session, "nonexistent@example.com")
    assert found_user is None

def test_create_user_with_invalid_role(db_session):
    invalid_data = {
        "email": f"invalid_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Invalid",
        "last_name": "Role",
        "phone": "+380509998877",
        "password": "password123",
        "role": "CUSTOMER"
    }

    with pytest.raises(ValueError, match="Invalid role: CUSTOMER"):
        create_user(db_session, invalid_data)

def test_create_user_guest_via_booking(db_session):
    guest_data = {
        "email": f"guest_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Guest",
        "last_name": "User",
        "phone": "+380501112233",
        "role": "GUEST"
    }

    user = create_user(db_session, guest_data, via_booking=True)
    db_session.commit()

    assert user is not None
    assert user.is_registered == False
    assert user.password is None