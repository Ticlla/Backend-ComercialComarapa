"""Product service for business logic.

This module provides the ProductService class that encapsulates
all business logic related to products.

Usage:
    from comercial_comarapa.services.product_service import ProductService
    from comercial_comarapa.db.database import get_db

    db = get_db()
    service = ProductService(db)
    products, pagination = service.list_products()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from comercial_comarapa.core.exceptions import (
    DuplicateSKUError,
    ProductNotFoundError,
)
from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.db.repositories.category import CategoryRepository
from comercial_comarapa.db.repositories.product import ProductRepository

if TYPE_CHECKING:
    from decimal import Decimal
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol
    from comercial_comarapa.models.common import PaginationMeta, PaginationParams
    from comercial_comarapa.models.product import (
        LowStockProduct,
        ProductCreate,
        ProductResponse,
        ProductUpdate,
    )

logger = get_logger(__name__)


class ProductService:
    """Service class for product business logic.

    Handles validation, business rules, and orchestrates
    repository operations for products.
    """

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize product service.

        Args:
            db: Database client.
        """
        self.repository = ProductRepository(db)
        self.category_repository = CategoryRepository(db)

    def list_products(
        self,
        pagination: PaginationParams | None = None,
        category_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        is_active: bool = True,
    ) -> tuple[list[ProductResponse], PaginationMeta]:
        """List products with filters and pagination.

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
        logger.info(
            "listing_products",
            page=pagination.page if pagination else 1,
            category_id=str(category_id) if category_id else None,
        )
        return self.repository.list_with_filters(
            pagination=pagination,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            is_active=is_active,
        )

    def get_product(self, product_id: UUID) -> ProductResponse:
        """Get a product by ID.

        Args:
            product_id: Product UUID.

        Returns:
            Product if found.

        Raises:
            ProductNotFoundError: If product not found.
        """
        logger.info("getting_product", product_id=str(product_id))
        product = self.repository.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product

    def get_product_by_sku(self, sku: str) -> ProductResponse:
        """Get a product by SKU.

        Args:
            sku: Product SKU.

        Returns:
            Product if found.

        Raises:
            ProductNotFoundError: If product not found.
        """
        logger.info("getting_product_by_sku", sku=sku)
        product = self.repository.get_by_sku(sku)
        if product is None:
            raise ProductNotFoundError(sku)
        return product

    def create_product(self, data: ProductCreate) -> ProductResponse:
        """Create a new product.

        Args:
            data: Product creation data.

        Returns:
            Created product.

        Raises:
            DuplicateSKUError: If SKU already exists.
        """
        logger.info("creating_product", sku=data.sku, name=data.name)

        # Check for duplicate SKU
        if self.repository.sku_exists(data.sku):
            raise DuplicateSKUError(data.sku)

        product = self.repository.create(data)
        logger.info("product_created", product_id=str(product.id), sku=product.sku)
        return product

    def update_product(
        self,
        product_id: UUID,
        data: ProductUpdate,
    ) -> ProductResponse:
        """Update an existing product.

        Args:
            product_id: Product UUID.
            data: Update data.

        Returns:
            Updated product.

        Raises:
            ProductNotFoundError: If product not found.
            DuplicateSKUError: If new SKU already exists.
        """
        logger.info("updating_product", product_id=str(product_id))

        # Verify product exists
        existing = self.repository.get_by_id(product_id)
        if existing is None:
            raise ProductNotFoundError(product_id)

        # Check for duplicate SKU if SKU is being changed
        if (
            data.sku
            and data.sku != existing.sku
            and self.repository.sku_exists(data.sku, exclude_id=str(product_id))
        ):
            raise DuplicateSKUError(data.sku)

        product = self.repository.update(product_id, data)
        if product is None:
            raise ProductNotFoundError(product_id)

        logger.info("product_updated", product_id=str(product_id))
        return product

    def delete_product(self, product_id: UUID) -> None:
        """Soft delete a product (set is_active=False).

        Args:
            product_id: Product UUID.

        Raises:
            ProductNotFoundError: If product not found.
        """
        logger.info("deleting_product", product_id=str(product_id))

        # Verify product exists
        if not self.repository.exists(product_id):
            raise ProductNotFoundError(product_id)

        # Soft delete by setting is_active=False
        from comercial_comarapa.models.product import ProductUpdate  # noqa: PLC0415

        self.repository.update(product_id, ProductUpdate(is_active=False))
        logger.info("product_soft_deleted", product_id=str(product_id))

    def search_products(
        self,
        term: str,
        limit: int = 20,
    ) -> list[ProductResponse]:
        """Search products by name or SKU.

        Args:
            term: Search term.
            limit: Maximum results.

        Returns:
            List of matching products.
        """
        logger.info("searching_products", term=term)
        return self.repository.search(term=term, limit=limit)

    def get_low_stock_products(self) -> list[LowStockProduct]:
        """Get products with stock below minimum level.

        Returns:
            List of low stock products.
        """
        logger.info("getting_low_stock_products")
        return self.repository.list_low_stock()

