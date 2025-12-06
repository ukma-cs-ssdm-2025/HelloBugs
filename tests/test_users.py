import pytest
from datetime import datetime
from src.api.services.user_service import (
    create_user, get_all_users, get_user_by_id,
    get_user_by_email, update_user_partial, delete_user,
    search_users, update_user_full
)
from src.api.models.user_model import User, UserRole
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import secrets
import uuid

@pytest.fixture
def test_user_dict():
    pwd = secrets.token_urlsafe(12)
    return {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Registered",
        "last_name": "User",
        "phone": "+380674567892",
        "password": pwd,
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
        password=generate_password_hash(secrets.token_urlsafe(12)),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_create_user_success(db_session, test_user_dict):
    user = create_user(db_session, test_user_dict)

    assert user is not None
    assert user.user_id is not None
    assert user.email == test_user_dict["email"]
    assert user.first_name == test_user_dict["first_name"]
    assert user.last_name == test_user_dict["last_name"]
    assert user.role == UserRole.GUEST
    assert user.is_registered == True
    assert check_password_hash(user.password, test_user_dict["password"])

def test_create_user_duplicate_email(db_session, existing_user):
    pwd2 = secrets.token_urlsafe(12)
    duplicate_data = {
        "email": existing_user.email,
        "first_name": "Second",
        "last_name": "User",
        "phone": "+380502222222",
        "password": pwd2,
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

    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.phone == "+380506667788"
    assert updated_user.email == existing_user.email

def test_update_user_password(db_session, existing_user):
    new_pwd = secrets.token_urlsafe(12)
    update_data = {"password": new_pwd}

    updated_user = update_user_partial(db_session, existing_user.user_id, update_data)

    assert check_password_hash(updated_user.password, new_pwd)

def test_delete_user(db_session, existing_user):
    result = delete_user(db_session, existing_user.user_id)

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
        "password": secrets.token_urlsafe(12),
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

    assert user is not None
    assert user.is_registered == False
    assert user.password is None


def test_create_user_missing_email(db_session):
    invalid_data = {
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501112233",
        "password": secrets.token_urlsafe(12),
        "role": "GUEST"
    }

    with pytest.raises(ValueError, match="Email is required and must be a string"):
        create_user(db_session, invalid_data)

def test_create_user_invalid_email_type(db_session):
    invalid_data = {
        "email": 12345,  
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501112233",
        "password": secrets.token_urlsafe(12),
        "role": "GUEST"
    }

    with pytest.raises(ValueError, match="Email is required and must be a string"):
        create_user(db_session, invalid_data)

def test_create_user_role_as_dict(db_session):
    user_data = {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501112233",
        "password": secrets.token_urlsafe(12),
        "role": {"value": "GUEST"}
    }

    user = create_user(db_session, user_data)
    assert user.role == UserRole.GUEST

def test_create_user_integrity_error(db_session, existing_user, monkeypatch):
    user_data = {
        "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": existing_user.phone,  
        "password": secrets.token_urlsafe(12),
        "role": "GUEST"
    }

    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        create_user(db_session, user_data)

def test_search_users_by_role(db_session, existing_user):
    users = search_users(db_session, role="GUEST")
    assert isinstance(users, list)
    assert len(users) > 0
    assert all(user.role == UserRole.GUEST for user in users)

def test_search_users_by_invalid_role(db_session):
    users = search_users(db_session, role="INVALID_ROLE")
    assert users == []

def test_search_users_by_last_name(db_session, existing_user):
    users = search_users(db_session, last_name="User")
    assert isinstance(users, list)
    assert len(users) > 0
    assert any(user.user_id == existing_user.user_id for user in users)

def test_search_users_by_role_and_last_name(db_session, existing_user):
    users = search_users(db_session, role="GUEST", last_name="User")
    assert isinstance(users, list)
    assert len(users) > 0

def test_update_user_partial_not_found(db_session):
    with pytest.raises(ValueError, match="User with ID 999999 not found"):
        update_user_partial(db_session, 999999, {"first_name": "Test"})

def test_update_user_partial_skip_protected_fields(db_session, existing_user):
    original_id = existing_user.user_id
    original_created_at = existing_user.created_at
    
    update_data = {
        "user_id": 99999,
        "id": 88888,
        "created_at": datetime.now(),
        "first_name": "NewName"
    }

    updated_user = update_user_partial(db_session, existing_user.user_id, update_data)
    
    assert updated_user.user_id == original_id
    assert updated_user.created_at == original_created_at
    assert updated_user.first_name == "NewName"

def test_update_user_partial_empty_password(db_session, existing_user):
    original_password = existing_user.password
    
    update_data = {"password": "   "}
    updated_user = update_user_partial(db_session, existing_user.user_id, update_data)
    
    assert updated_user.password == original_password

def test_update_user_partial_role_as_dict(db_session, existing_user):
    update_data = {"role": {"value": "ADMIN"}}
    updated_user = update_user_partial(db_session, existing_user.user_id, update_data)
    
    assert updated_user.role == UserRole.ADMIN

def test_update_user_partial_invalid_role(db_session, existing_user):
    update_data = {"role": "INVALID_ROLE"}
    
    with pytest.raises(ValueError, match="Invalid role: INVALID_ROLE"):
        update_user_partial(db_session, existing_user.user_id, update_data)

def test_update_user_partial_integrity_error(db_session, existing_user):
    second_user = User(
        email=f"second_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Second",
        last_name="User",
        phone="+380509998877",
        is_registered=True,
        password=generate_password_hash(secrets.token_urlsafe(12)),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(second_user)
    db_session.commit()

    update_data = {"email": second_user.email}
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        update_user_partial(db_session, existing_user.user_id, update_data)

def test_update_user_full_success(db_session, existing_user):
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "UpdatedFirst",
        "last_name": "UpdatedLast",
        "phone": "+380501234567",
        "role": "ADMIN"
    }

    updated_user = update_user_full(db_session, existing_user.user_id, update_data)
    
    assert updated_user.email == update_data["email"]
    assert updated_user.first_name == update_data["first_name"]
    assert updated_user.last_name == update_data["last_name"]
    assert updated_user.phone == update_data["phone"]
    assert updated_user.role == UserRole.ADMIN

def test_update_user_full_not_found(db_session):
    update_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST"
    }

    with pytest.raises(ValueError, match="User with ID 999999 not found"):
        update_user_full(db_session, 999999, update_data)

def test_update_user_full_missing_fields(db_session, existing_user):
    incomplete_data = {
        "email": "test@example.com",
        "first_name": "Test"
    }

    with pytest.raises(ValueError, match="Missing required fields for full update"):
        update_user_full(db_session, existing_user.user_id, incomplete_data)

def test_update_user_full_role_as_dict(db_session, existing_user):
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": {"value": "ADMIN"}
    }

    updated_user = update_user_full(db_session, existing_user.user_id, update_data)
    assert updated_user.role == UserRole.ADMIN

def test_update_user_full_invalid_role(db_session, existing_user):
    update_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "INVALID"
    }

    with pytest.raises(ValueError, match="Invalid role: INVALID"):
        update_user_full(db_session, existing_user.user_id, update_data)

def test_update_user_full_with_password(db_session, existing_user):
    new_pwd = secrets.token_urlsafe(12)
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST",
        "password": new_pwd
    }

    updated_user = update_user_full(db_session, existing_user.user_id, update_data)
    assert check_password_hash(updated_user.password, new_pwd)

def test_update_user_full_empty_password(db_session, existing_user):
    original_password = existing_user.password
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST",
        "password": "   "
    }

    updated_user = update_user_full(db_session, existing_user.user_id, update_data)
    assert updated_user.password == original_password

def test_update_user_full_integrity_error(db_session, existing_user):
    second_user = User(
        email=f"second_{uuid.uuid4().hex[:8]}@example.com",
        first_name="Second",
        last_name="User",
        phone="+380509998877",
        is_registered=True,
        password=generate_password_hash(secrets.token_urlsafe(12)),
        role=UserRole.GUEST,
        created_at=datetime.now()
    )
    db_session.add(second_user)
    db_session.commit()

    update_data = {
        "email": second_user.email,
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST"
    }

    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        update_user_full(db_session, existing_user.user_id, update_data)

def test_delete_user_not_found(db_session):
    with pytest.raises(ValueError, match="User with ID 999999 not found"):
        delete_user(db_session, 999999)


def test_search_users_with_empty_role_string(db_session, existing_user):
    """Test search with empty role string (should return empty list)"""
    users = search_users(db_session, role="   ", last_name=None)
    assert isinstance(users, list)
    assert users == []

def test_search_users_with_empty_last_name_string(db_session, existing_user):
    """Test search with empty last_name string (should return empty list)"""
    users = search_users(db_session, role=None, last_name="   ")
    assert isinstance(users, list)
    assert users == []

def test_search_users_with_both_empty_strings(db_session, existing_user):
    """Test search with both parameters as empty strings (should return empty list)"""
    users = search_users(db_session, role="   ", last_name="   ")
    assert isinstance(users, list)
    assert users == []

def test_search_users_no_match_last_name(db_session, existing_user):
    """Test search with last_name that doesn't match any user"""
    users = search_users(db_session, last_name="NonExistentLastName12345")
    assert users == []

def test_create_user_database_error(db_session, test_user_dict, monkeypatch):
    """Test create_user when database commit fails with SQLAlchemyError"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(Exception, match="Database error creating user"):
        create_user(db_session, test_user_dict)

def test_update_user_partial_database_error(db_session, existing_user, monkeypatch):
    """Test update_user_partial when database commit fails"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(Exception, match="Database error updating user"):
        update_user_partial(db_session, existing_user.user_id, {"first_name": "Test"})

def test_update_user_full_database_error(db_session, existing_user, monkeypatch):
    """Test update_user_full when database commit fails"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST"
    }
    
    with pytest.raises(Exception, match="Database error updating user"):
        update_user_full(db_session, existing_user.user_id, update_data)

def test_delete_user_database_error(db_session, existing_user, monkeypatch):
    """Test delete_user when database commit fails"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(Exception, match="Database error deleting user"):
        delete_user(db_session, existing_user.user_id)

def test_create_user_integrity_error_without_email_match(db_session, existing_user, monkeypatch):
    """Test IntegrityError handling in create_user (non-email constraint violation)"""
    def mock_add(user):
        pass
    
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    
    monkeypatch.setattr(db_session, "add", mock_add)
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    user_data = {
        "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "password": secrets.token_urlsafe(12),
        "role": "GUEST"
    }
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        create_user(db_session, user_data)

def test_update_user_partial_integrity_error_without_match(db_session, existing_user, monkeypatch):
    """Test IntegrityError handling in update_user_partial (non-email/phone constraint)"""
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    update_data = {"first_name": "Test"}
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        update_user_partial(db_session, existing_user.user_id, update_data)

def test_update_user_full_integrity_error_without_match(db_session, existing_user, monkeypatch):
    """Test IntegrityError handling in update_user_full (non-email/phone constraint)"""
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST"
    }
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        update_user_full(db_session, existing_user.user_id, update_data)


def test_search_users_with_empty_role_string(db_session, existing_user):
    """Test search with empty role string (should return empty list)"""
    users = search_users(db_session, role="   ", last_name=None)
    assert isinstance(users, list)
    assert users == []

def test_search_users_with_empty_last_name_string(db_session, existing_user):
    """Test search with empty last_name string (should return empty list)"""
    users = search_users(db_session, role=None, last_name="   ")
    assert isinstance(users, list)
    assert users == []

def test_search_users_with_both_empty_strings(db_session, existing_user):
    """Test search with both parameters as empty strings (should return empty list)"""
    users = search_users(db_session, role="   ", last_name="   ")
    assert isinstance(users, list)
    assert users == []

def test_search_users_no_match_last_name(db_session, existing_user):
    """Test search with last_name that doesn't match any user"""
    users = search_users(db_session, last_name="NonExistentLastName12345")
    assert users == []

def test_create_user_database_error(db_session, test_user_dict, monkeypatch):
    """Test create_user when database commit fails with SQLAlchemyError"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(Exception, match="Database error creating user"):
        create_user(db_session, test_user_dict)

def test_update_user_partial_database_error(db_session, existing_user, monkeypatch):
    """Test update_user_partial when database commit fails"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(Exception, match="Database error updating user"):
        update_user_partial(db_session, existing_user.user_id, {"first_name": "Test"})

def test_update_user_full_database_error(db_session, existing_user, monkeypatch):
    """Test update_user_full when database commit fails"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST"
    }
    
    with pytest.raises(Exception, match="Database error updating user"):
        update_user_full(db_session, existing_user.user_id, update_data)

def test_create_user_integrity_error_without_email_match(db_session, test_user_dict, monkeypatch):
    """Test IntegrityError handling in create_user (non-email constraint violation)"""
    
    original_query = db_session.query
    def mock_query(model):
        mock_obj = original_query(model)
        original_filter_by = mock_obj.filter_by
        def mock_filter_by(**kwargs):
            result = original_filter_by(**kwargs)
            original_first = result.first
            result.first = lambda: None  
            return result
        mock_obj.filter_by = mock_filter_by
        return mock_obj
    
    monkeypatch.setattr(db_session, "query", mock_query)
    
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        create_user(db_session, test_user_dict)

def test_update_user_partial_integrity_error_without_match(db_session, existing_user, monkeypatch):
    """Test IntegrityError handling in update_user_partial (non-email/phone constraint)"""
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    update_data = {"first_name": "Test"}
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        update_user_partial(db_session, existing_user.user_id, update_data)

def test_update_user_full_integrity_error_without_match(db_session, existing_user, monkeypatch):
    """Test IntegrityError handling in update_user_full (non-email/phone constraint)"""
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    update_data = {
        "email": f"updated_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501234567",
        "role": "GUEST"
    }
    
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        update_user_full(db_session, existing_user.user_id, update_data)

def test_delete_user_database_error(db_session, existing_user, monkeypatch):
    """Test delete_user when database commit fails"""
    def mock_commit():
        raise SQLAlchemyError("Database error")
    
    monkeypatch.setattr(db_session, "commit", mock_commit)
    
    with pytest.raises(Exception, match="Database error deleting user"):
        delete_user(db_session, existing_user.user_id)


def test_create_user_password_hashing(db_session):
    pwd = secrets.token_urlsafe(12)
    user_data = {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+380501112233",
        "password": pwd,
        "role": "GUEST"
    }
    user = create_user(db_session, user_data, via_booking=False)
    assert check_password_hash(user.password, pwd)

def test_create_user_via_booking_sets_unregistered(db_session):
    user_data = {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Booking",
        "last_name": "Guest",
        "phone": "+380501122334",
        "role": "GUEST"
    }
    user = create_user(db_session, user_data, via_booking=True)
    assert user.is_registered is False
    assert user.password is None

def test_create_user_role_as_string_and_dict(db_session):
    for role_input in ["ADMIN", {"value": "ADMIN"}]:
        user_data = {
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "first_name": "RoleTest",
            "last_name": "User",
            "phone": f"+38050{secrets.randbelow(9999999):07d}",  # унікальний телефон
            "password": secrets.token_urlsafe(12),
            "role": role_input
        }
        user = create_user(db_session, user_data)
        assert user.role.name == "ADMIN"

def test_create_user_integrity_error_email_conflict(db_session, monkeypatch):
    def mock_commit():
        raise IntegrityError("statement", "params", "orig")
    monkeypatch.setattr(db_session, "commit", mock_commit)

    user_data = {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "first_name": "Integrity",
        "last_name": "Error",
        "phone": "+380501144556",
        "password": secrets.token_urlsafe(12),
        "role": "GUEST"
    }
    with pytest.raises(ValueError, match="User with this email or phone already exists"):
        create_user(db_session, user_data)

def test_search_users_role_and_last_name_empty_strings(db_session, existing_user):
    result = search_users(db_session, role="   ", last_name="   ")
    assert result == []

def test_search_users_role_empty_last_name_valid(db_session, existing_user):
    # strip пробіли та None для ролі
    result = search_users(
        db_session,
        role=None,
        last_name=existing_user.last_name.strip()
    )
    assert any(user.user_id == existing_user.user_id for user in result)

def test_search_users_role_valid_last_name_empty(db_session, existing_user):
    result = search_users(
        db_session,
        role="GUEST",
        last_name=None  # пусте прізвище
    )
    assert any(user.user_id == existing_user.user_id for user in result)