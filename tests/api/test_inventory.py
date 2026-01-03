"""Tests for Inventory API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from comercial_comarapa.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_product(client: TestClient) -> dict:
    """Create a sample product for testing."""
    product_data = {
        "sku": f"INV-TEST-{uuid4().hex[:8].upper()}",
        "name": "Inventory Test Product",
        "unit_price": 10.00,
    }
    response = client.post("/api/v1/products", json=product_data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["data"]


class TestListMovements:
    """Tests for GET /api/v1/inventory/movements."""

    def test_list_movements_returns_200(self, client: TestClient):
        """GET /movements returns 200."""
        response = client.get("/api/v1/inventory/movements")
        assert response.status_code == status.HTTP_200_OK

    def test_list_movements_returns_paginated_response(self, client: TestClient):
        """Response includes pagination metadata."""
        response = client.get("/api/v1/inventory/movements")
        data = response.json()

        assert "success" in data
        assert "data" in data
        assert "pagination" in data
        assert data["success"] is True

    def test_list_movements_pagination_params(self, client: TestClient):
        """Pagination parameters are applied."""
        response = client.get("/api/v1/inventory/movements?page=1&page_size=5")
        data = response.json()

        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 5


class TestGetMovementsByProduct:
    """Tests for GET /api/v1/inventory/movements/{product_id}."""

    def test_get_movements_product_not_found(self, client: TestClient):
        """GET movements for non-existent product returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/inventory/movements/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_movements_returns_list(
        self, client: TestClient, sample_product: dict
    ):
        """GET movements for product returns list."""
        product_id = sample_product["id"]

        # Create a movement first
        client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 10},
        )

        response = client.get(f"/api/v1/inventory/movements/{product_id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1


class TestStockEntry:
    """Tests for POST /api/v1/inventory/entry."""

    def test_stock_entry_success(self, client: TestClient, sample_product: dict):
        """POST /entry increases product stock."""
        product_id = sample_product["id"]
        initial_stock = sample_product["current_stock"]

        response = client.post(
            "/api/v1/inventory/entry",
            json={
                "product_id": product_id,
                "quantity": 50,
                "reason": "PURCHASE",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["success"] is True
        assert data["data"]["previous_stock"] == initial_stock
        assert data["data"]["new_stock"] == initial_stock + 50
        assert data["data"]["movement_type"] == "ENTRY"
        assert data["data"]["quantity"] == 50

    def test_stock_entry_product_not_found(self, client: TestClient):
        """POST /entry with non-existent product returns 404."""
        fake_id = uuid4()
        response = client.post(
            "/api/v1/inventory/entry",
            json={
                "product_id": str(fake_id),
                "quantity": 10,
                "reason": "PURCHASE",
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_stock_entry_with_notes(self, client: TestClient, sample_product: dict):
        """POST /entry can include notes."""
        product_id = sample_product["id"]

        response = client.post(
            "/api/v1/inventory/entry",
            json={
                "product_id": product_id,
                "quantity": 20,
                "reason": "PURCHASE",
                "notes": "Initial stock from supplier",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["notes"] == "Initial stock from supplier"

    def test_stock_entry_invalid_quantity(self, client: TestClient, sample_product: dict):
        """POST /entry with zero or negative quantity returns 422."""
        product_id = sample_product["id"]

        response = client.post(
            "/api/v1/inventory/entry",
            json={
                "product_id": product_id,
                "quantity": 0,
                "reason": "PURCHASE",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_stock_entry_updates_product(self, client: TestClient, sample_product: dict):
        """Stock entry updates product's current_stock."""
        product_id = sample_product["id"]
        initial_stock = sample_product["current_stock"]

        # Add stock
        client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 100},
        )

        # Verify product stock updated
        product_response = client.get(f"/api/v1/products/{product_id}")
        assert product_response.json()["data"]["current_stock"] == initial_stock + 100


class TestStockExit:
    """Tests for POST /api/v1/inventory/exit."""

    def test_stock_exit_success(self, client: TestClient, sample_product: dict):
        """POST /exit decreases product stock."""
        product_id = sample_product["id"]

        # First add some stock
        client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 100},
        )

        # Get current stock
        product_response = client.get(f"/api/v1/products/{product_id}")
        current_stock = product_response.json()["data"]["current_stock"]

        # Exit some stock
        response = client.post(
            "/api/v1/inventory/exit",
            json={
                "product_id": product_id,
                "quantity": 30,
                "reason": "SALE",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["data"]["previous_stock"] == current_stock
        assert data["data"]["new_stock"] == current_stock - 30
        assert data["data"]["movement_type"] == "EXIT"

    def test_stock_exit_insufficient_stock(self, client: TestClient, sample_product: dict):
        """POST /exit with qty > stock returns 400."""
        product_id = sample_product["id"]

        response = client.post(
            "/api/v1/inventory/exit",
            json={
                "product_id": product_id,
                "quantity": 9999,
                "reason": "DAMAGE",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "INSUFFICIENT_STOCK"

    def test_stock_exit_product_not_found(self, client: TestClient):
        """POST /exit with non-existent product returns 404."""
        fake_id = uuid4()
        response = client.post(
            "/api/v1/inventory/exit",
            json={
                "product_id": str(fake_id),
                "quantity": 10,
                "reason": "SALE",
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStockAdjustment:
    """Tests for POST /api/v1/inventory/adjustment."""

    def test_stock_adjustment_success(self, client: TestClient, sample_product: dict):
        """POST /adjustment sets exact stock value."""
        product_id = sample_product["id"]

        response = client.post(
            "/api/v1/inventory/adjustment",
            json={
                "product_id": product_id,
                "new_stock": 75,
                "reason": "CORRECTION",
                "notes": "Physical count adjustment",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["data"]["new_stock"] == 75
        assert data["data"]["movement_type"] == "ADJUSTMENT"

    def test_stock_adjustment_updates_product(
        self, client: TestClient, sample_product: dict
    ):
        """Adjustment updates product's current_stock to exact value."""
        product_id = sample_product["id"]

        client.post(
            "/api/v1/inventory/adjustment",
            json={
                "product_id": product_id,
                "new_stock": 42,
                "reason": "CORRECTION",
            },
        )

        # Verify product stock
        product_response = client.get(f"/api/v1/products/{product_id}")
        assert product_response.json()["data"]["current_stock"] == 42

    def test_stock_adjustment_product_not_found(self, client: TestClient):
        """POST /adjustment with non-existent product returns 404."""
        fake_id = uuid4()
        response = client.post(
            "/api/v1/inventory/adjustment",
            json={
                "product_id": str(fake_id),
                "new_stock": 100,
                "reason": "CORRECTION",
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_stock_adjustment_no_change_returns_400(
        self, client: TestClient, sample_product: dict
    ):
        """POST /adjustment with same stock value returns 400."""
        product_id = sample_product["id"]
        current_stock = sample_product["current_stock"]

        response = client.post(
            "/api/v1/inventory/adjustment",
            json={
                "product_id": product_id,
                "new_stock": current_stock,  # Same as current
                "reason": "CORRECTION",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "INVALID_OPERATION"


class TestMovementHistory:
    """Tests for movement history and ordering."""

    def test_movements_ordered_by_date_desc(
        self, client: TestClient, sample_product: dict
    ):
        """Movements are returned newest first."""
        product_id = sample_product["id"]

        # Create multiple movements
        client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 10},
        )
        client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 20},
        )
        client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 30},
        )

        response = client.get(f"/api/v1/inventory/movements/{product_id}")
        movements = response.json()["data"]

        # Most recent (quantity=30) should be first
        assert movements[0]["quantity"] == 30
        assert movements[1]["quantity"] == 20
        assert movements[2]["quantity"] == 10

    def test_movement_records_previous_stock(
        self, client: TestClient, sample_product: dict
    ):
        """Movement record contains correct previous_stock."""
        product_id = sample_product["id"]
        initial_stock = sample_product["current_stock"]

        # First entry
        response1 = client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 50},
        )
        assert response1.json()["data"]["previous_stock"] == initial_stock
        assert response1.json()["data"]["new_stock"] == initial_stock + 50

        # Second entry
        response2 = client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 25},
        )
        assert response2.json()["data"]["previous_stock"] == initial_stock + 50
        assert response2.json()["data"]["new_stock"] == initial_stock + 75

    def test_movement_includes_product_info(
        self, client: TestClient, sample_product: dict
    ):
        """Movement response includes product name and SKU."""
        product_id = sample_product["id"]

        response = client.post(
            "/api/v1/inventory/entry",
            json={"product_id": product_id, "quantity": 10},
        )

        data = response.json()["data"]
        assert data["product_name"] == sample_product["name"]
        assert data["product_sku"] == sample_product["sku"]

