import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.app import app as flask_app
from src.api.db import Base, get_db
from src.api.config import TestingConfig
import os
from src.api.models.booking_model import Booking
from src.api.models.room_model import RoomAmenity, Room, Amenity
from src.api.models.user_model import User

TEST_DATABASE_URL = os.getenv("DATABASE_URL", TestingConfig.DATABASE_URL)

engine = create_engine(TEST_DATABASE_URL)
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
    if not hasattr(flask_app, 'dependency_overrides'):
        flask_app.dependency_overrides = {}

    flask_app.config.from_object(TestingConfig)
    flask_app.config['TESTING'] = True

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
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def cleanup_data():

    yield

    session = TestingSessionLocal()
    try:
        session.query(Booking).delete(synchronize_session=False)
        session.query(RoomAmenity).delete(synchronize_session=False)
        session.query(Room).delete(synchronize_session=False)
        session.query(User).delete(synchronize_session=False)
        session.query(Amenity).delete(synchronize_session=False)

        session.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        session.rollback()
    finally:
        session.close()