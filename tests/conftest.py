"""Pytest configuration and fixtures.

This module provides shared fixtures for all tests.
"""

import pytest
from fastapi.testclient import TestClient

from comercial_comarapa.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application.

    Returns:
        TestClient instance for making test requests.
    """
    return TestClient(app)

