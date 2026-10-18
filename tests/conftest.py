"""Pytest fixtures for API testing and database sessions."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import app
from app.db import get_db


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture providing an HTTP client bound to the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yield a database session from the application session dependency."""
    yield from get_db()
