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

from typing import TYPE_CHECKING

from comercial_comarapa.db.repositories.base import BaseRepository
from comercial_comarapa.models.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

if TYPE_CHECKING:
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol


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

    def list_low_stock(self) -> list[ProductResponse]:
        """List products with stock below minimum level.

        Returns:
            List of products with low stock.
        """
        # Note: This requires a custom query since we need current_stock < min_stock_level
        # For now, we'll use the view if available, otherwise fetch all and filter
        result = (
            self.db.table("v_low_stock_products")
            .select("*")
            .execute()
        )
        return [self.response_model.model_validate(row) for row in result.data or []]

