"""Product repository for data access.

This module provides the ProductRepository for managing product entities.

Usage:
    from comercial_comarapa.db.repositories.product import ProductRepository
    from comercial_comarapa.db.database import get_db

    db = get_db()
    repo = ProductRepository(db)
    products, pagination = repo.list()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from comercial_comarapa.core.logging import get_logger, log_db_query
from comercial_comarapa.db.repositories.base import BaseRepository
from comercial_comarapa.models.common import PaginationMeta, PaginationParams
from comercial_comarapa.models.product import (
    LowStockProduct,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol

logger = get_logger(__name__)


class ProductRepository(BaseRepository[ProductResponse, ProductCreate, ProductUpdate]):
    """Repository for Product entities."""

    table_name = "products"
    response_model = ProductResponse
    entity_name = "Product"

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize product repository.

        Args:
            db: Database client.
        """
        super().__init__(db)

    def get_by_sku(self, sku: str) -> ProductResponse | None:
        """Get product by SKU.

        Args:
            sku: Product SKU.

        Returns:
            Product if found, None otherwise.
        """
        result = (
            self.db.table(self.table_name)
            .select("*")
            .eq("sku", sku)
            .single()
            .execute()
        )

        if result.data:
            return self.response_model.model_validate(result.data)
        return None

    def sku_exists(self, sku: str, exclude_id: str | None = None) -> bool:
        """Check if a product SKU already exists.

        Args:
            sku: Product SKU to check.
            exclude_id: Optional ID to exclude (for updates).

        Returns:
            True if SKU exists, False otherwise.
        """
        query = self.db.table(self.table_name).select("id").eq("sku", sku)

        if exclude_id:
            query = query.neq("id", exclude_id)

        result = query.execute()
        return len(result.data or []) > 0

    def has_products_for_category(self, category_id: UUID) -> bool:
        """Check if a category has any active products.

        Args:
            category_id: Category UUID to check.

        Returns:
            True if category has active products, False otherwise.
        """
        result = (
            self.db.table(self.table_name)
            .select("id")
            .eq("category_id", str(category_id))
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return len(result.data or []) > 0

    def list_by_category(
        self,
        category_id: UUID,
        include_inactive: bool = False,
    ) -> list[ProductResponse]:
        """List all products in a category.

        Args:
            category_id: Category UUID.
            include_inactive: If True, include inactive products.

        Returns:
            List of products in the category.
        """
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("category_id", str(category_id))
        )

        if not include_inactive:
            query = query.eq("is_active", True)

        result = query.order("name").execute()
        return [self.response_model.model_validate(row) for row in result.data or []]

    def list_low_stock(self) -> list[LowStockProduct]:
        """List products with stock below minimum level.

        Returns:
            List of low stock products from the database view.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        result = (
            self.db.table("v_low_stock_products")
            .select("*")
            .execute()
        )

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SELECT", "v_low_stock_products", duration_ms)

        return [LowStockProduct.model_validate(row) for row in result.data or []]

    def list_with_filters(
        self,
        pagination: PaginationParams | None = None,
        category_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        is_active: bool = True,
    ) -> tuple[list[ProductResponse], PaginationMeta]:
        """List products with advanced filters.

        Args:
            pagination: Pagination parameters.
            category_id: Filter by category.
            min_price: Minimum unit price.
            max_price: Maximum unit price.
            in_stock: Filter by stock availability.
            is_active: Filter by active status.

        Returns:
            Tuple of (products list, pagination metadata).
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        if pagination is None:
            pagination = PaginationParams()

        # Build filters dict
        filters: dict[str, Any] = {"is_active": is_active}

        if category_id:
            filters["category_id"] = str(category_id)

        # Build query
        query = self.db.table(self.table_name).select("*")

        # Apply basic filters
        for column, value in filters.items():
            if value is not None:
                query = query.eq(column, value)

        # Apply price filters
        if min_price is not None:
            query = query.gte("unit_price", float(min_price))

        if max_price is not None:
            query = query.lte("unit_price", float(max_price))

        # Apply in_stock filter
        if in_stock is True:
            query = query.gt("current_stock", 0)
        elif in_stock is False:
            query = query.eq("current_stock", 0)

        # Apply ordering and pagination
        query = query.order("name")

        start_idx = pagination.offset
        end_idx = start_idx + pagination.page_size - 1
        query = query.range(start_idx, end_idx)

        result = query.execute()

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query(
            "SELECT",
            self.table_name,
            duration_ms,
            page=pagination.page,
            filters=bool(category_id or min_price or max_price or in_stock is not None),
        )

        # Parse results
        entities = [self.response_model.model_validate(row) for row in result.data or []]

        # Get total count (need to rebuild query for count without pagination)
        total_items = self._count_with_filters(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            is_active=is_active,
        )

        pagination_meta = PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total_items,
        )

        return entities, pagination_meta

    def _count_with_filters(
        self,
        category_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        is_active: bool = True,
    ) -> int:
        """Count products matching filters.

        Args:
            category_id: Filter by category.
            min_price: Minimum unit price.
            max_price: Maximum unit price.
            in_stock: Filter by stock availability.
            is_active: Filter by active status.

        Returns:
            Count of matching products.
        """
        query = self.db.table(self.table_name).select("id").eq("is_active", is_active)

        if category_id:
            query = query.eq("category_id", str(category_id))

        if min_price is not None:
            query = query.gte("unit_price", float(min_price))

        if max_price is not None:
            query = query.lte("unit_price", float(max_price))

        if in_stock is True:
            query = query.gt("current_stock", 0)
        elif in_stock is False:
            query = query.eq("current_stock", 0)

        return query.count()

    def search(
        self,
        term: str,
        is_active: bool = True,
        limit: int = 20,
    ) -> list[ProductResponse]:
        """Search products by name or SKU.

        Note: This is a simplified search that fetches products and filters in Python.
        For production, consider using PostgreSQL full-text search or ILIKE.

        Args:
            term: Search term (case-insensitive).
            is_active: Filter by active status.
            limit: Maximum results to return.

        Returns:
            List of matching products.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        # Fetch active products and filter in Python
        # Note: In production, use PostgreSQL ILIKE or full-text search
        result = (
            self.db.table(self.table_name)
            .select("*")
            .eq("is_active", is_active)
            .order("name")
            .execute()
        )

        term_lower = term.lower()
        matches = []
        for row in result.data or []:
            name = row.get("name", "").lower()
            sku = row.get("sku", "").lower()
            if term_lower in name or term_lower in sku:
                matches.append(self.response_model.model_validate(row))
                if len(matches) >= limit:
                    break

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SEARCH", self.table_name, duration_ms, term=term, results=len(matches))

        return matches


