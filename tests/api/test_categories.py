"""Tests for Categories API endpoints.

All tests use mock database - NO real database calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from fastapi import status

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestListCategories:
    """Tests for GET /api/v1/categories."""

    def test_list_categories_returns_200(self, client: TestClient) -> None:
        """GET /categories returns 200."""
        response = client.get("/api/v1/categories")
        assert response.status_code == status.HTTP_200_OK

    def test_list_categories_returns_paginated_response(
        self, client: TestClient
    ) -> None:
        """Response includes pagination metadata."""
        response = client.get("/api/v1/categories")
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert "pagination" in data
        assert data["success"] is True

    def test_list_categories_pagination_params(self, client: TestClient) -> None:
        """Pagination parameters are applied."""
        response = client.get("/api/v1/categories?page=1&page_size=5")
        data = response.json()

        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 5

    def test_list_categories_invalid_page(self, client: TestClient) -> None:
        """Invalid page parameter returns 422."""
        response = client.get("/api/v1/categories?page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_categories_invalid_page_size(self, client: TestClient) -> None:
        """Invalid page_size parameter returns 422."""
        response = client.get("/api/v1/categories?page_size=200")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCategory:
    """Tests for GET /api/v1/categories/{id}."""

    def test_get_category_not_found(self, client: TestClient) -> None:
        """GET non-existent category returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/categories/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_category_not_found_error_format(self, client: TestClient) -> None:
        """404 error has correct format."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/categories/{fake_id}")
        data = response.json()

        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "CATEGORY_NOT_FOUND"

    def test_get_category_invalid_uuid(self, client: TestClient) -> None:
        """Invalid UUID returns 422."""
        response = client.get("/api/v1/categories/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateCategory:
    """Tests for POST /api/v1/categories."""

    def test_create_category_success(self, client: TestClient) -> None:
        """POST valid category returns 201."""
        response = client.post(
            "/api/v1/categories",
            json={"name": f"Test Category {uuid4().hex[:8]}"},
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_category_returns_created_data(self, client: TestClient) -> None:
        """Created category includes all fields."""
        name = f"Test Category {uuid4().hex[:8]}"
        response = client.post(
            "/api/v1/categories",
            json={"name": name, "description": "Test description"},
        )
        data = response.json()

        assert data["success"] is True
        assert data["data"]["name"] == name
        assert data["data"]["description"] == "Test description"
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    def test_create_category_name_required(self, client: TestClient) -> None:
        """Name is required."""
        response = client.post("/api/v1/categories", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_category_name_too_long(self, client: TestClient) -> None:
        """Name max length is 100 chars."""
        response = client.post(
            "/api/v1/categories",
            json={"name": "x" * 101},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_category_duplicate_name(self, client: TestClient) -> None:
        """Duplicate name returns 409."""
        name = f"Duplicate Test {uuid4().hex[:8]}"

        # Create first category
        response1 = client.post("/api/v1/categories", json={"name": name})
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create with same name
        response2 = client.post("/api/v1/categories", json={"name": name})
        assert response2.status_code == status.HTTP_409_CONFLICT

    def test_create_category_duplicate_error_format(self, client: TestClient) -> None:
        """409 error has correct format."""
        name = f"Duplicate Error Test {uuid4().hex[:8]}"

        client.post("/api/v1/categories", json={"name": name})
        response = client.post("/api/v1/categories", json={"name": name})
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "DUPLICATE_ENTITY"


class TestUpdateCategory:
    """Tests for PUT /api/v1/categories/{id}."""

    def test_update_category_success(self, client: TestClient) -> None:
        """PUT updates category."""
        # Create category
        name = f"Update Test {uuid4().hex[:8]}"
        create_response = client.post("/api/v1/categories", json={"name": name})
        category_id = create_response.json()["data"]["id"]

        # Update it
        new_name = f"Updated {uuid4().hex[:8]}"
        response = client.put(
            f"/api/v1/categories/{category_id}",
            json={"name": new_name},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["name"] == new_name

    def test_update_category_not_found(self, client: TestClient) -> None:
        """PUT non-existent category returns 404."""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/categories/{fake_id}",
            json={"name": "New Name"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_category_partial(self, client: TestClient) -> None:
        """Partial update only changes specified fields."""
        # Create category
        name = f"Partial Update Test {uuid4().hex[:8]}"
        create_response = client.post(
            "/api/v1/categories",
            json={"name": name, "description": "Original description"},
        )
        category_id = create_response.json()["data"]["id"]

        # Update only description
        response = client.put(
            f"/api/v1/categories/{category_id}",
            json={"description": "Updated description"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["name"] == name
        assert data["description"] == "Updated description"

    def test_update_category_duplicate_name(self, client: TestClient) -> None:
        """Update to existing name returns 409."""
        name1 = f"First Category {uuid4().hex[:8]}"
        name2 = f"Second Category {uuid4().hex[:8]}"

        # Create two categories
        client.post("/api/v1/categories", json={"name": name1})
        response2 = client.post("/api/v1/categories", json={"name": name2})
        category2_id = response2.json()["data"]["id"]

        # Try to update second to first's name
        response = client.put(
            f"/api/v1/categories/{category2_id}",
            json={"name": name1},
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestDeleteCategory:
    """Tests for DELETE /api/v1/categories/{id}."""

    def test_delete_category_success(self, client: TestClient) -> None:
        """DELETE removes category."""
        # Create category
        name = f"Delete Test {uuid4().hex[:8]}"
        create_response = client.post("/api/v1/categories", json={"name": name})
        category_id = create_response.json()["data"]["id"]

        # Delete it
        response = client.delete(f"/api/v1/categories/{category_id}")
        assert response.status_code == status.HTTP_200_OK

        # Verify it's gone
        get_response = client.get(f"/api/v1/categories/{category_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_category_not_found(self, client: TestClient) -> None:
        """DELETE non-existent category returns 404."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/categories/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_category_response_format(self, client: TestClient) -> None:
        """DELETE returns correct response format."""
        # Create category
        name = f"Delete Format Test {uuid4().hex[:8]}"
        create_response = client.post("/api/v1/categories", json={"name": name})
        category_id = create_response.json()["data"]["id"]

        # Delete it
        response = client.delete(f"/api/v1/categories/{category_id}")
        data = response.json()

        assert data["success"] is True
        assert data["id"] == category_id
        assert "message" in data
