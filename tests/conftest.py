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

@pytest.fixture(scope="session")
def prepare_database():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    
    yield
    
    try:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
    except Exception:
        pass

@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    flask_app.config.from_object(TestingConfig)
    return flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()