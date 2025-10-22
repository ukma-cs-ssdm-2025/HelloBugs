# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.app import app as flask_app
from src.api.db import Base
from src.api.config import TestingConfig
import os

TEST_DATABASE_URL = os.getenv("DATABASE_URL", TestingConfig.DATABASE_URL)

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 2}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """Створює таблиці перед всіма тестами"""
    Base.metadata.drop_all(bind=engine)  # Очищаємо старі дані
    Base.metadata.create_all(bind=engine)
    print("\n✅ База даних ініціалізована")

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    flask_app.config.from_object(TestingConfig)
    return flask_app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def cleanup_between_tests():
    """Очищає всі дані між тестами для ізоляції"""
    yield

    # Після кожного тесту очищаємо таблиці
    session = TestingSessionLocal()
    try:
        from src.api.models.room_model import Room, RoomAmenity
        session.query(RoomAmenity).delete()
        session.query(Room).delete()
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()