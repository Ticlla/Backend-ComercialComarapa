"""Pytest configuration and fixtures.

This module provides shared fixtures for all tests including
mock database client that prevents tests from hitting real DB.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from comercial_comarapa.db.database import get_db
from comercial_comarapa.main import app

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# Mock Database Client Implementation
# =============================================================================


class MockQueryResult:
    """Mock query result that mimics DatabaseClientProtocol results."""

    def __init__(self, data: Any = None):
        self._data = data

    @property
    def data(self) -> Any:
        return self._data


class MockTableQuery:
    """Mock table query builder with in-memory storage.

    Supports method chaining and basic CRUD operations.
    """

    def __init__(self, storage: dict[str, list[dict]], table_name: str):
        self._storage = storage
        self._table_name = table_name
        self._filters: list[tuple[str, str, Any]] = []
        self._selected_columns: str = "*"
        self._limit_count: int | None = None
        self._range_start: int | None = None
        self._range_end: int | None = None
        self._order_column: str | None = None
        self._order_desc: bool = False
        self._single: bool = False

        # Initialize table if not exists
        if table_name not in self._storage:
            self._storage[table_name] = []

    def select(self, columns: str = "*") -> MockTableQuery:
        self._selected_columns = columns
        return self

    def eq(self, column: str, value: Any) -> MockTableQuery:
        self._filters.append((column, "eq", value))
        return self

    def neq(self, column: str, value: Any) -> MockTableQuery:
        self._filters.append((column, "neq", value))
        return self

    def gt(self, column: str, value: Any) -> MockTableQuery:
        self._filters.append((column, "gt", value))
        return self

    def gte(self, column: str, value: Any) -> MockTableQuery:
        self._filters.append((column, "gte", value))
        return self

    def lt(self, column: str, value: Any) -> MockTableQuery:
        self._filters.append((column, "lt", value))
        return self

    def lte(self, column: str, value: Any) -> MockTableQuery:
        self._filters.append((column, "lte", value))
        return self

    def ilike(self, column: str, pattern: str) -> MockTableQuery:
        self._filters.append((column, "ilike", pattern))
        return self

    def limit(self, count: int) -> MockTableQuery:
        self._limit_count = count
        return self

    def range(self, start: int, end: int) -> MockTableQuery:
        self._range_start = start
        self._range_end = end
        return self

    def order(self, column: str, desc: bool = False) -> MockTableQuery:
        self._order_column = column
        self._order_desc = desc
        return self

    def single(self) -> MockTableQuery:
        self._single = True
        return self

    def _apply_filters(self, records: list[dict]) -> list[dict]:
        """Apply filters to records."""
        result = records.copy()

        for column, op, value in self._filters:
            if op == "eq":
                result = [r for r in result if str(r.get(column)) == str(value)]
            elif op == "neq":
                result = [r for r in result if str(r.get(column)) != str(value)]
            elif op == "gt":
                result = [r for r in result if r.get(column, 0) > value]
            elif op == "gte":
                result = [r for r in result if r.get(column, 0) >= value]
            elif op == "lt":
                result = [r for r in result if r.get(column, 0) < value]
            elif op == "lte":
                result = [r for r in result if r.get(column, 0) <= value]
            elif op == "ilike":
                # Simple ILIKE implementation
                search = value.replace("%", "").lower()
                result = [r for r in result if search in str(r.get(column, "")).lower()]

        return result

    def _apply_ordering(self, records: list[dict]) -> list[dict]:
        """Apply ordering to records."""
        if self._order_column:
            return sorted(
                records,
                key=lambda r: r.get(self._order_column, ""),
                reverse=self._order_desc,
            )
        return records

    def _apply_pagination(self, records: list[dict]) -> list[dict]:
        """Apply pagination to records."""
        if self._range_start is not None and self._range_end is not None:
            return records[self._range_start : self._range_end + 1]
        if self._limit_count is not None:
            return records[: self._limit_count]
        return records

    def execute(self) -> MockQueryResult:
        """Execute SELECT query."""
        records = self._storage.get(self._table_name, [])
        records = self._apply_filters(records)
        records = self._apply_ordering(records)
        records = self._apply_pagination(records)

        if self._single:
            return MockQueryResult(records[0] if records else None)

        return MockQueryResult(records)

    def count(self) -> int:
        """Execute COUNT query."""
        records = self._storage.get(self._table_name, [])
        records = self._apply_filters(records)
        return len(records)

    def insert(self, data: dict[str, Any]) -> MockQueryResult:
        """Insert a record."""
        # Generate ID and timestamps if not provided
        record = data.copy()
        if "id" not in record:
            record["id"] = str(uuid4())
        if "created_at" not in record:
            record["created_at"] = datetime.now().isoformat()
        if "updated_at" not in record:
            record["updated_at"] = datetime.now().isoformat()

        # Set defaults for products
        if self._table_name == "products":
            record.setdefault("current_stock", 0)
            record.setdefault("is_active", True)

        self._storage[self._table_name].append(record)
        return MockQueryResult([record])

    def update(self, data: dict[str, Any]) -> MockQueryResult:
        """Update records matching filters."""
        records = self._storage.get(self._table_name, [])
        filtered = self._apply_filters(records)
        updated = []

        for record in filtered:
            record.update(data)
            record["updated_at"] = datetime.now().isoformat()
            updated.append(record)

        return MockQueryResult(updated)

    def delete(self) -> MockQueryResult:
        """Delete records matching filters."""
        records = self._storage.get(self._table_name, [])
        filtered = self._apply_filters(records)
        deleted = []

        for record in filtered:
            if record in records:
                records.remove(record)
                deleted.append(record)

        return MockQueryResult(deleted)


class MockRPCQuery:
    """Mock RPC query builder."""

    def __init__(self, func_name: str, params: dict[str, Any], storage: dict):
        self._func_name = func_name
        self._params = params
        self._storage = storage

    def execute(self) -> MockQueryResult:
        """Execute RPC query - returns mock search results."""
        if self._func_name == "search_products_fuzzy":
            # Return empty results for search
            return MockQueryResult([])
        return MockQueryResult([])


class MockDatabaseClient:
    """Mock database client that stores data in memory.

    This class mimics the DatabaseClientProtocol for testing purposes.
    All data is stored in-memory and isolated per test.
    """

    def __init__(self) -> None:
        self._storage: dict[str, list[dict]] = {}

    def table(self, name: str) -> MockTableQuery:
        """Get a mock table query builder."""
        return MockTableQuery(self._storage, name)

    def rpc(self, name: str, params: dict[str, Any]) -> MockRPCQuery:
        """Mock RPC call."""
        return MockRPCQuery(name, params, self._storage)

    def execute_atomic_stock_update(
        self,
        product_id: str,
        delta: int,
    ) -> tuple[int, int]:
        """Atomically update product stock."""
        products = self._storage.get("products", [])
        for product in products:
            if str(product.get("id")) == str(product_id):
                previous = product.get("current_stock", 0)
                new_stock = previous + delta
                product["current_stock"] = new_stock
                return (previous, new_stock)
        raise ValueError(f"Product {product_id} not found")

    def execute_atomic_stock_set(
        self,
        product_id: str,
        new_stock: int,
    ) -> tuple[int, int]:
        """Atomically set product stock."""
        products = self._storage.get("products", [])
        for product in products:
            if str(product.get("id")) == str(product_id):
                previous = product.get("current_stock", 0)
                product["current_stock"] = new_stock
                return (previous, new_stock)
        raise ValueError(f"Product {product_id} not found")

    def close(self) -> None:
        """Close connection (no-op for mock)."""
        pass

    def clear(self) -> None:
        """Clear all stored data (useful between tests)."""
        self._storage.clear()


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture
def mock_db() -> MockDatabaseClient:
    """Create a fresh mock database client for each test.

    Returns:
        MockDatabaseClient instance with empty storage.
    """
    return MockDatabaseClient()


@pytest.fixture
def client(mock_db: MockDatabaseClient) -> Generator[TestClient, None, None]:
    """Create a test client with mocked database.

    This fixture automatically overrides the database dependency
    so tests don't hit the real database.

    Args:
        mock_db: Mock database client fixture.

    Yields:
        TestClient instance for making test requests.
    """
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: mock_db

    yield TestClient(app)

    # Clean up after test
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_real_db() -> TestClient:
    """Create a test client that uses the real database.

    USE WITH CAUTION: This fixture connects to the real database.
    Only use for integration tests that explicitly need real DB access.

    Returns:
        TestClient instance with real DB connection.
    """
    return TestClient(app)
