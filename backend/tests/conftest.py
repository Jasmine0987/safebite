import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """A FastAPI test client — makes requests in-process, no real server needed."""
    return TestClient(app)