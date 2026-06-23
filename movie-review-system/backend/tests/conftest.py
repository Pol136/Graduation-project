import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.main import app


def _database_available() -> bool:
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except OperationalError:
        return False


requires_db = pytest.mark.skipif(
    not _database_available(),
    reason="PostgreSQL database is not available",
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def unique_email() -> str:
    return f"user_{uuid.uuid4().hex}@example.com"
