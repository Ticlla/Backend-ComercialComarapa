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
        result = self.db.table(self.table_name).select("*").eq("sku", sku).single().execute()

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

    def update_stock(self, product_id: UUID, new_stock: int) -> ProductResponse | None:
        """Update product stock level.

        Args:
            product_id: Product UUID.
            new_stock: New stock value.

        Returns:
            Updated product if found, None otherwise.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        result = (
            self.db.table(self.table_name)
            .eq("id", str(product_id))
            .update({"current_stock": new_stock})
        ).data

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("UPDATE_STOCK", self.table_name, duration_ms, id=str(product_id))

        if result and len(result) > 0:
            return self.response_model.model_validate(result[0])
        return None

    def atomic_stock_delta(self, product_id: UUID, delta: int) -> tuple[int, int]:
        """Atomically update stock by delta and return previous/new values.

        This prevents race conditions by using a single UPDATE statement.

        Args:
            product_id: Product UUID.
            delta: Amount to add (positive) or subtract (negative).

        Returns:
            Tuple of (previous_stock, new_stock).

        Raises:
            DatabaseError: If product not found.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()
        previous, new = self.db.execute_atomic_stock_update(str(product_id), delta)
        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query(
            "ATOMIC_STOCK_DELTA",
            self.table_name,
            duration_ms,
            id=str(product_id),
            delta=delta,
        )
        return previous, new

    def atomic_stock_set(self, product_id: UUID, new_stock: int) -> tuple[int, int]:
        """Atomically set stock and return previous/new values.

        This prevents race conditions by using a single UPDATE statement.

        Args:
            product_id: Product UUID.
            new_stock: Absolute new stock value.

        Returns:
            Tuple of (previous_stock, new_stock).

        Raises:
            DatabaseError: If product not found.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()
        previous, new = self.db.execute_atomic_stock_set(str(product_id), new_stock)
        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query(
            "ATOMIC_STOCK_SET",
            self.table_name,
            duration_ms,
            id=str(product_id),
            new_stock=new_stock,
        )
        return previous, new

    def get_current_stock(self, product_id: UUID) -> int | None:
        """Get current stock for a product.

        Args:
            product_id: Product UUID.

        Returns:
            Current stock if product found, None otherwise.
        """
        result = (
            self.db.table(self.table_name)
            .select("current_stock")
            .eq("id", str(product_id))
            .single()
            .execute()
        )

        if result.data:
            return result.data.get("current_stock")
        return None

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
        query = self.db.table(self.table_name).select("*").eq("category_id", str(category_id))

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

        result = self.db.table("v_low_stock_products").select("*").execute()

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SELECT", "v_low_stock_products", duration_ms)

        return [LowStockProduct.model_validate(row) for row in result.data or []]

    def _apply_filters(
        self,
        query: Any,
        category_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        is_active: bool = True,
    ) -> Any:
        """Apply common filters to a query (B5: extracted shared logic).

        Args:
            query: The query builder to apply filters to.
            category_id: Filter by category.
            min_price: Minimum unit price.
            max_price: Maximum unit price.
            in_stock: Filter by stock availability.
            is_active: Filter by active status.

        Returns:
            Query with filters applied.
        """
        query = query.eq("is_active", is_active)

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

        return query

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

        # Build query with shared filter logic
        query = self.db.table(self.table_name).select("*")
        query = self._apply_filters(
            query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            is_active=is_active,
        )

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

        # Get total count using shared filter logic
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
        query = self.db.table(self.table_name).select("id")
        query = self._apply_filters(
            query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            is_active=is_active,
        )
        return query.count()

    def search_by_name(
        self,
        term: str,
        is_active: bool = True,
        limit: int = 20,
    ) -> list[ProductResponse]:
        """Search products by name using database ILIKE.

        Args:
            term: Search term (case-insensitive).
            is_active: Filter by active status.
            limit: Maximum results to return.

        Returns:
            List of matching products.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        # Use ILIKE for database-level case-insensitive search
        pattern = f"%{term}%"
        result = (
            self.db.table(self.table_name)
            .select("*")
            .eq("is_active", is_active)
            .ilike("name", pattern)
            .order("name")
            .limit(limit)
            .execute()
        )

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SEARCH_NAME", self.table_name, duration_ms, term=term)

        return [self.response_model.model_validate(row) for row in result.data or []]

    def search_by_sku(
        self,
        term: str,
        is_active: bool = True,
        limit: int = 20,
    ) -> list[ProductResponse]:
        """Search products by SKU using database ILIKE.

        Args:
            term: Search term (case-insensitive).
            is_active: Filter by active status.
            limit: Maximum results to return.

        Returns:
            List of matching products.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        pattern = f"%{term}%"
        result = (
            self.db.table(self.table_name)
            .select("*")
            .eq("is_active", is_active)
            .ilike("sku", pattern)
            .order("sku")
            .limit(limit)
            .execute()
        )

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SEARCH_SKU", self.table_name, duration_ms, term=term)

        return [self.response_model.model_validate(row) for row in result.data or []]

    def search(
        self,
        term: str,
        is_active: bool = True,
        limit: int = 20,
    ) -> list[ProductResponse]:
        """Search products using hybrid search (FTS + Trigram).

        Engineering Note: We delegate the heavy lifting to the database RPC
        function 'search_products_hybrid' for performance and accuracy.

        Args:
            term: Search term.
            is_active: Filter by active status (handled by RPC).
            limit: Maximum results to return.

        Returns:
            List of matching products ranked by relevance.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        # 1. Guard against non-string or null inputs
        safe_term = str(term or "").strip()

        # 2. Return empty immediately if term is empty to save DB resources
        if not safe_term:
            return []

        # 3. Call the Hybrid Search RPC
        # The RPC function 'search_products_hybrid' already handles:
        # - unaccenting and trimming
        # - active status filtering (currently hardcoded in RPC, but could be param)
        # - FTS ranking and Trigram similarity
        result = self.db.rpc(
            "search_products_hybrid",
            {
                "search_term": safe_term,
                "result_limit": limit,
                "similarity_threshold": 0.15,  # Lower for better typo tolerance in longer strings
                "is_active_filter": is_active,
            },
        ).execute()

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query(
            "SEARCH_HYBRID",
            self.table_name,
            duration_ms,
            term=safe_term,
            results=len(result.data or []),
        )

        return [self.response_model.model_validate(row) for row in result.data or []]
