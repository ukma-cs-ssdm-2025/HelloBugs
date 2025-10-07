import pytest
from src.api.app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    flask_app.config.update({
        'TESTING': True,
    })
    return flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
