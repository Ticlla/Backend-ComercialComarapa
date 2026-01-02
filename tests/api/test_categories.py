"""Tests for Categories API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from comercial_comarapa.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestListCategories:
    """Tests for GET /api/v1/categories."""

    def test_list_categories_returns_200(self, client: TestClient):
        """GET /categories returns 200."""
        response = client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK

    def test_list_categories_returns_paginated_response(self, client: TestClient):
        """Response includes pagination metadata."""
        response = client.get("/api/v1/categories")
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert "pagination" in data
        assert data["success"] is True


class TestGetCategory:
    """Tests for GET /api/v1/categories/id."""

    def test_get_category_not_found(self, client: TestClient):
        """GET non-existent category returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/categories/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateCategory:
    """Tests for POST /api/v1/categories."""

    def test_create_category_success(self, client: TestClient):
        """POST valid category returns 201."""
        response = client.post(
            "/api/v1/categories",
            json={"name": f"Test Category {uuid4().hex[:8]}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_category_name_required(self, client: TestClient):
        """Name is required."""
        response = client.post("/api/v1/categories", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateCategory:
    """Tests for PUT /api/v1/categories/id."""

    def test_update_category_not_found(self, client: TestClient):
        """PUT non-existent category returns 404."""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/categories/{fake_id}",
            json={"name": "New Name"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteCategory:
    """Tests for DELETE /api/v1/categories/id."""

    def test_delete_category_not_found(self, client: TestClient):
        """DELETE non-existent category returns 404."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/categories/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
