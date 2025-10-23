import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.api.app import app as flask_app
from src.api.db import Base, get_db
from src.api.config import TestingConfig
import os

TEST_DATABASE_URL = os.getenv("DATABASE_URL", TestingConfig.DATABASE_URL)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    """Підготовка БД для тестів"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def app():
    """Фікстура додатку"""
    flask_app.config.from_object(TestingConfig)
    flask_app.config['TESTING'] = True

    # Перевизначаємо get_db для тестів
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    flask_app.dependency_overrides[get_db] = override_get_db
    return flask_app


@pytest.fixture
def db_session():
    """Фікстура сесії БД для сервісів"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(app):
    """Фікстура тестового клієнта"""
    return app.test_client()


@pytest.fixture(autouse=True)
def cleanup_data(db_session):
    """Очищення даних після кожного тесту"""
    yield
    try:
        db_session.execute(text("DELETE FROM bookings"))
        db_session.execute(text("DELETE FROM room_amenities"))
        db_session.execute(text("DELETE FROM rooms"))
        db_session.execute(text("DELETE FROM users"))
        db_session.execute(text("DELETE FROM amenities"))
        db_session.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        db_session.rollback()