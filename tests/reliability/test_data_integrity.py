import pytest
from src.api.models.user_model import User, UserRole
from src.api.db import db
import uuid


@pytest.fixture
def guest_user(db_session):
    """
    Створює "гостьового" користувача в БД, який нібито
    раніше створив бронювання без реєстрації.
    """
    guest_email = f"guest_{uuid.uuid4().hex[:10]}@example.com"
    user = User(
        email=guest_email,
        first_name="Guest",
        last_name="User",
        phone="+38000000000",
        is_registered=False,
        role=UserRole.GUEST
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_register_upgrades_guest_account(client, guest_user):
    """
    Гість, який раніше бронював (is_registered=False),
    тепер може успішно зареєструватися з тією ж поштою.
    """
    registration_data = {
        "email": guest_user.email,
        "password": "a_very_secure_password123",
        "first_name": "Registered",
        "last_name": "Guest",
        "phone": guest_user.phone
    }

    response = client.post("/api/v1/auth/register", json=registration_data)
    assert response.status_code == 201

    session = db()
    updated_user = session.query(User).filter_by(email=guest_user.email).first()
    assert updated_user is not None

    assert updated_user.user_id == guest_user.user_id

    assert updated_user.is_registered is True
    assert updated_user.role == UserRole.GUEST
    assert updated_user.password is not None
    assert updated_user.check_password("a_very_secure_password123") is True

    assert updated_user.first_name == "Registered"

    user_count = session.query(User).filter_by(email=guest_user.email).count()
    assert user_count == 1