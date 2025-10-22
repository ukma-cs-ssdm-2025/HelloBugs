import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.api.app import app as flask_app
from src.api.db import Base
from src.api.config import TestingConfig
import os

TEST_DATABASE_URL = os.getenv("DATABASE_URL", TestingConfig.DATABASE_URL)

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 5,
        "options": "-c statement_timeout=10000"
    }
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def app():
    flask_app.config.from_object(TestingConfig)
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def cleanup_data():

    yield

    session = TestingSessionLocal()
    try:
        # 1. Спочатку bookings (залежить від rooms, users)
        session.execute(text("DELETE FROM bookings"))

        # 2. Потім проміжні таблиці
        session.execute(text("DELETE FROM room_amenities"))

        # 3. Потім основні таблиці
        session.execute(text("DELETE FROM rooms"))
        session.execute(text("DELETE FROM users"))
        session.execute(text("DELETE FROM amenities"))

        session.commit()

    except Exception as e:
        print(f"Cleanup error: {e}")
        session.rollback()
    finally:
        session.close()