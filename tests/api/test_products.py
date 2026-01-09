"""Tests for Products API endpoints.

All tests use mock database - NO real database calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi import status

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


@pytest.fixture
def sample_product_data() -> dict:
    """Create sample product data."""
    return {
        "sku": f"TEST-{uuid4().hex[:8].upper()}",
        "name": "Test Product",
        "description": "A test product description",
        "unit_price": 25.50,
        "cost_price": 18.00,
        "min_stock_level": 10,
    }


class TestListProducts:
    """Tests for GET /api/v1/products."""

    def test_list_products_returns_200(self, client: TestClient) -> None:
        """GET /products returns 200."""
        response = client.get("/api/v1/products")
        assert response.status_code == status.HTTP_200_OK

    def test_list_products_returns_paginated_response(self, client: TestClient) -> None:
        """Response includes pagination metadata."""
        response = client.get("/api/v1/products")
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert "pagination" in data
        assert data["success"] is True

    def test_list_products_pagination_params(self, client: TestClient) -> None:
        """Pagination parameters are applied."""
        response = client.get("/api/v1/products?page=1&page_size=5")
        data = response.json()

        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 5

    def test_list_products_invalid_page(self, client: TestClient) -> None:
        """Invalid page parameter returns 422."""
        response = client.get("/api/v1/products?page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_products_invalid_page_size(self, client: TestClient) -> None:
        """Invalid page_size parameter returns 422."""
        response = client.get("/api/v1/products?page_size=200")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_products_filter_by_category(self, client: TestClient) -> None:
        """Can filter products by category_id."""
        fake_category_id = uuid4()
        response = client.get(f"/api/v1/products?category_id={fake_category_id}")
        assert response.status_code == status.HTTP_200_OK

    def test_list_products_filter_by_price_range(self, client: TestClient) -> None:
        """Can filter products by price range."""
        response = client.get("/api/v1/products?min_price=10&max_price=100")
        assert response.status_code == status.HTTP_200_OK

    def test_list_products_filter_in_stock(self, client: TestClient) -> None:
        """Can filter products by stock availability."""
        response = client.get("/api/v1/products?in_stock=true")
        assert response.status_code == status.HTTP_200_OK

    def test_list_products_filter_inactive(self, client: TestClient) -> None:
        """Can list inactive products."""
        response = client.get("/api/v1/products?is_active=false")
        assert response.status_code == status.HTTP_200_OK


class TestGetProduct:
    """Tests for GET /api/v1/products/{id}."""

    def test_get_product_not_found(self, client: TestClient) -> None:
        """GET non-existent product returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/products/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_product_not_found_error_format(self, client: TestClient) -> None:
        """404 error has correct format."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/products/{fake_id}")
        data = response.json()

        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "PRODUCT_NOT_FOUND"

    def test_get_product_invalid_uuid(self, client: TestClient) -> None:
        """Invalid UUID returns 422."""
        response = client.get("/api/v1/products/not-a-uuid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetProductBySku:
    """Tests for GET /api/v1/products/sku/{sku}."""

    def test_get_product_by_sku_not_found(self, client: TestClient) -> None:
        """GET non-existent SKU returns 404."""
        response = client.get("/api/v1/products/sku/NONEXISTENT-SKU")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_product_by_sku_success(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """GET existing SKU returns product."""
        # Create product first
        create_response = client.post("/api/v1/products", json=sample_product_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        sku = create_response.json()["data"]["sku"]

        # Get by SKU
        response = client.get(f"/api/v1/products/sku/{sku}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["sku"] == sku


class TestCreateProduct:
    """Tests for POST /api/v1/products."""

    def test_create_product_success(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """POST valid product returns 201."""
        response = client.post("/api/v1/products", json=sample_product_data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_product_returns_created_data(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Created product includes all fields."""
        response = client.post("/api/v1/products", json=sample_product_data)
        data = response.json()

        assert data["success"] is True
        assert data["data"]["sku"] == sample_product_data["sku"]
        assert data["data"]["name"] == sample_product_data["name"]
        assert "id" in data["data"]
        assert "created_at" in data["data"]
        assert data["data"]["current_stock"] == 0
        assert data["data"]["is_active"] is True

    def test_create_product_sku_required(self, client: TestClient) -> None:
        """SKU is required."""
        response = client.post(
            "/api/v1/products",
            json={"name": "Test", "unit_price": 10.0},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_product_name_required(self, client: TestClient) -> None:
        """Name is required."""
        response = client.post(
            "/api/v1/products",
            json={"sku": "TEST-001", "unit_price": 10.0},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_product_price_required(self, client: TestClient) -> None:
        """Unit price is required."""
        response = client.post(
            "/api/v1/products",
            json={"sku": "TEST-001", "name": "Test"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_product_negative_price(self, client: TestClient) -> None:
        """Negative price returns 422."""
        response = client.post(
            "/api/v1/products",
            json={
                "sku": "TEST-001",
                "name": "Test",
                "unit_price": -10.0,
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_product_duplicate_sku(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Duplicate SKU returns 409."""
        # Create first product
        response1 = client.post("/api/v1/products", json=sample_product_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create with same SKU
        response2 = client.post("/api/v1/products", json=sample_product_data)
        assert response2.status_code == status.HTTP_409_CONFLICT

    def test_create_product_duplicate_error_format(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """409 error has correct format."""
        client.post("/api/v1/products", json=sample_product_data)
        response = client.post("/api/v1/products", json=sample_product_data)
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "DUPLICATE_SKU"


class TestUpdateProduct:
    """Tests for PUT /api/v1/products/{id}."""

    def test_update_product_success(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """PUT updates product."""
        # Create product
        create_response = client.post("/api/v1/products", json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        # Update it
        new_name = "Updated Product Name"
        response = client.put(
            f"/api/v1/products/{product_id}",
            json={"name": new_name},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["name"] == new_name

    def test_update_product_not_found(self, client: TestClient) -> None:
        """PUT non-existent product returns 404."""
        fake_id = uuid4()
        response = client.put(
            f"/api/v1/products/{fake_id}",
            json={"name": "New Name"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_product_partial(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Partial update only changes specified fields."""
        # Create product
        create_response = client.post("/api/v1/products", json=sample_product_data)
        product_id = create_response.json()["data"]["id"]
        original_name = create_response.json()["data"]["name"]

        # Update only price
        new_price = 99.99
        response = client.put(
            f"/api/v1/products/{product_id}",
            json={"unit_price": new_price},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["name"] == original_name
        assert float(data["unit_price"]) == new_price

    def test_update_product_duplicate_sku(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Update to existing SKU returns 409."""
        # Create two products
        product1_data = sample_product_data.copy()
        product1_data["sku"] = f"FIRST-{uuid4().hex[:6].upper()}"

        product2_data = sample_product_data.copy()
        product2_data["sku"] = f"SECOND-{uuid4().hex[:6].upper()}"

        client.post("/api/v1/products", json=product1_data)
        response2 = client.post("/api/v1/products", json=product2_data)
        product2_id = response2.json()["data"]["id"]

        # Try to update second to first's SKU
        response = client.put(
            f"/api/v1/products/{product2_id}",
            json={"sku": product1_data["sku"]},
        )
        assert response.status_code == status.HTTP_409_CONFLICT


class TestDeleteProduct:
    """Tests for DELETE /api/v1/products/{id}."""

    def test_delete_product_success(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """DELETE soft-deletes product."""
        # Create product
        create_response = client.post("/api/v1/products", json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        # Delete it
        response = client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == status.HTTP_200_OK

        # Product should still exist but be inactive
        get_response = client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["data"]["is_active"] is False

    def test_delete_product_not_found(self, client: TestClient) -> None:
        """DELETE non-existent product returns 404."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/products/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_product_response_format(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """DELETE returns correct response format."""
        # Create product
        create_response = client.post("/api/v1/products", json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        # Delete it
        response = client.delete(f"/api/v1/products/{product_id}")
        data = response.json()

        assert data["success"] is True
        assert data["id"] == product_id
        assert "message" in data

    def test_deleted_product_not_in_active_list(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Soft-deleted products not returned in default list."""
        # Create product
        create_response = client.post("/api/v1/products", json=sample_product_data)
        product_id = create_response.json()["data"]["id"]
        sku = create_response.json()["data"]["sku"]

        # Delete it
        client.delete(f"/api/v1/products/{product_id}")

        # Check it's not in active list
        list_response = client.get("/api/v1/products")
        products = list_response.json()["data"]
        product_skus = [p["sku"] for p in products]
        assert sku not in product_skus


class TestSearchProducts:
    """Tests for GET /api/v1/products/search."""

    def test_search_products_returns_200(self, client: TestClient) -> None:
        """Search returns 200."""
        response = client.get("/api/v1/products/search?q=test")
        assert response.status_code == status.HTTP_200_OK

    def test_search_products_requires_query(self, client: TestClient) -> None:
        """Search requires q parameter."""
        response = client.get("/api/v1/products/search")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_products_min_length(self, client: TestClient) -> None:
        """Search query must be at least 1 character."""
        response = client.get("/api/v1/products/search?q=")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLowStockProducts:
    """Tests for GET /api/v1/products/low-stock."""

    def test_low_stock_returns_200(self, client: TestClient) -> None:
        """Low stock endpoint returns 200."""
        response = client.get("/api/v1/products/low-stock")
        assert response.status_code == status.HTTP_200_OK

    def test_low_stock_response_format(self, client: TestClient) -> None:
        """Low stock returns correct format."""
        response = client.get("/api/v1/products/low-stock")
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)


class TestPriceRangeValidation:
    """Tests for price range validation (B6 fix)."""

    def test_valid_price_range(self, client: TestClient) -> None:
        """Valid price range returns 200."""
        response = client.get("/api/v1/products?min_price=10&max_price=100")
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_price_range(self, client: TestClient) -> None:
        """min_price > max_price returns 422."""
        response = client.get("/api/v1/products?min_price=100&max_price=10")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_price_range_error_format(self, client: TestClient) -> None:
        """Invalid price range has correct error format."""
        response = client.get("/api/v1/products?min_price=100&max_price=10")
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_PRICE_RANGE"


class TestCategoryValidation:
    """Tests for category validation (B3 fix)."""

    def test_create_product_invalid_category(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Create with non-existent category returns 404."""
        sample_product_data["category_id"] = str(uuid4())
        response = client.post("/api/v1/products", json=sample_product_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_product_invalid_category_error_format(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Invalid category error has correct format."""
        sample_product_data["category_id"] = str(uuid4())
        response = client.post("/api/v1/products", json=sample_product_data)
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "CATEGORY_NOT_FOUND"

    def test_update_product_invalid_category(
        self, client: TestClient, sample_product_data: dict
    ) -> None:
        """Update with non-existent category returns 404."""
        # Create product without category
        create_response = client.post("/api/v1/products", json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        # Try to update with invalid category
        response = client.put(
            f"/api/v1/products/{product_id}",
            json={"category_id": str(uuid4())},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
