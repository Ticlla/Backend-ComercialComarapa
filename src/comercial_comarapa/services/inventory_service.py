"""Inventory service for business logic.

This module provides the InventoryService class that encapsulates
all business logic related to inventory movements.

Usage:
    from comercial_comarapa.services.inventory_service import InventoryService
    from comercial_comarapa.db.database import get_db

    db = get_db()
    service = InventoryService(db)
    movement = service.stock_entry(product_id, quantity=50, reason="PURCHASE")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from comercial_comarapa.core.exceptions import (
    DatabaseError,
    InsufficientStockError,
    InvalidOperationError,
    ProductNotFoundError,
)
from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.db.repositories.inventory import InventoryRepository
from comercial_comarapa.db.repositories.product import ProductRepository
from comercial_comarapa.models.inventory import (
    MovementReason,
    MovementType,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol
    from comercial_comarapa.models.common import PaginationMeta, PaginationParams
    from comercial_comarapa.models.inventory import (
        MovementResponse,
        StockAdjustmentRequest,
        StockEntryRequest,
        StockExitRequest,
    )

logger = get_logger(__name__)


class InventoryService:
    """Service class for inventory business logic.

    Handles stock entries, exits, adjustments, and movement history.
    All stock operations use atomic database updates to prevent race conditions.
    """

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize inventory service.

        Args:
            db: Database client.
        """
        self.repository = InventoryRepository(db)
        self.product_repository = ProductRepository(db)

    def stock_entry(self, data: StockEntryRequest) -> MovementResponse:
        """Add stock to a product (entry).

        Uses atomic stock update to prevent race conditions.

        Args:
            data: Stock entry request with product_id, quantity, reason, notes.

        Returns:
            Created movement record.

        Raises:
            ProductNotFoundError: If product not found.
        """
        logger.info(
            "stock_entry",
            product_id=str(data.product_id),
            quantity=data.quantity,
            reason=data.reason.value,
        )

        # Atomically update stock and get previous/new values
        try:
            previous_stock, new_stock = self.product_repository.atomic_stock_delta(
                data.product_id, delta=data.quantity
            )
        except DatabaseError as e:
            if "Product not found" in str(e):
                raise ProductNotFoundError(data.product_id) from e
            raise

        # Create movement record
        movement = self.repository.create(
            product_id=data.product_id,
            movement_type=MovementType.ENTRY,
            quantity=data.quantity,
            reason=data.reason,
            previous_stock=previous_stock,
            new_stock=new_stock,
            notes=data.notes,
        )

        logger.info(
            "stock_entry_completed",
            product_id=str(data.product_id),
            previous_stock=previous_stock,
            new_stock=new_stock,
        )

        return movement

    def stock_exit(self, data: StockExitRequest) -> MovementResponse:
        """Remove stock from a product (exit).

        Uses atomic stock check-and-update to prevent race conditions.

        Args:
            data: Stock exit request with product_id, quantity, reason, notes.

        Returns:
            Created movement record.

        Raises:
            ProductNotFoundError: If product not found.
            InsufficientStockError: If not enough stock available.
        """
        logger.info(
            "stock_exit",
            product_id=str(data.product_id),
            quantity=data.quantity,
            reason=data.reason.value,
        )

        # First check if product exists and has sufficient stock
        current_stock = self.product_repository.get_current_stock(data.product_id)
        if current_stock is None:
            raise ProductNotFoundError(data.product_id)

        if data.quantity > current_stock:
            raise InsufficientStockError(
                product_id=data.product_id,
                requested=data.quantity,
                available=current_stock,
            )

        # Atomically update stock with negative delta
        try:
            previous_stock, new_stock = self.product_repository.atomic_stock_delta(
                data.product_id, delta=-data.quantity
            )
        except DatabaseError as e:
            if "Product not found" in str(e):
                raise ProductNotFoundError(data.product_id) from e
            raise

        # Create movement record
        movement = self.repository.create(
            product_id=data.product_id,
            movement_type=MovementType.EXIT,
            quantity=data.quantity,
            reason=data.reason,
            previous_stock=previous_stock,
            new_stock=new_stock,
            notes=data.notes,
        )

        logger.info(
            "stock_exit_completed",
            product_id=str(data.product_id),
            previous_stock=previous_stock,
            new_stock=new_stock,
        )

        return movement

    def stock_adjustment(self, data: StockAdjustmentRequest) -> MovementResponse:
        """Adjust stock to a specific value.

        Uses atomic stock update to prevent race conditions.

        Args:
            data: Stock adjustment request with product_id, new_stock, reason, notes.

        Returns:
            Created movement record.

        Raises:
            ProductNotFoundError: If product not found.
            InvalidOperationError: If new_stock equals current stock (no change).
        """
        logger.info(
            "stock_adjustment",
            product_id=str(data.product_id),
            new_stock=data.new_stock,
            reason=data.reason.value,
        )

        # Check current stock first to validate and reject no-change adjustments
        current_stock = self.product_repository.get_current_stock(data.product_id)
        if current_stock is None:
            raise ProductNotFoundError(data.product_id)

        # B3 Fix: Reject adjustments that don't change stock
        if data.new_stock == current_stock:
            raise InvalidOperationError(
                f"Stock adjustment rejected: new_stock ({data.new_stock}) equals "
                f"current_stock ({current_stock}). No change needed.",
                details={
                    "product_id": str(data.product_id),
                    "current_stock": current_stock,
                    "requested_stock": data.new_stock,
                },
            )

        # Atomically set stock and get previous/new values
        try:
            previous_stock, new_stock = self.product_repository.atomic_stock_set(
                data.product_id, data.new_stock
            )
        except DatabaseError as e:
            if "Product not found" in str(e):
                raise ProductNotFoundError(data.product_id) from e
            raise

        # Calculate quantity as absolute difference
        quantity = abs(new_stock - previous_stock)

        # Create movement record
        movement = self.repository.create(
            product_id=data.product_id,
            movement_type=MovementType.ADJUSTMENT,
            quantity=quantity,
            reason=data.reason,
            previous_stock=previous_stock,
            new_stock=new_stock,
            notes=data.notes,
        )

        logger.info(
            "stock_adjustment_completed",
            product_id=str(data.product_id),
            previous_stock=previous_stock,
            new_stock=new_stock,
        )

        return movement

    def get_movements_by_product(
        self,
        product_id: UUID,
        limit: int = 50,
    ) -> list[MovementResponse]:
        """Get movement history for a product.

        Args:
            product_id: Product UUID.
            limit: Maximum movements to return.

        Returns:
            List of movements, newest first.

        Raises:
            ProductNotFoundError: If product not found.
        """
        logger.info("getting_movements", product_id=str(product_id))

        # Verify product exists
        if not self.product_repository.exists(product_id):
            raise ProductNotFoundError(product_id)

        return self.repository.list_by_product(product_id, limit=limit)

    def list_movements(
        self,
        pagination: PaginationParams | None = None,
        product_id: UUID | None = None,
        movement_type: MovementType | None = None,
        reason: MovementReason | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[MovementResponse], PaginationMeta]:
        """List all movements with filters and pagination.

        Args:
            pagination: Pagination parameters.
            product_id: Filter by product.
            movement_type: Filter by movement type.
            reason: Filter by reason.
            date_from: Filter by start date.
            date_to: Filter by end date.

        Returns:
            Tuple of (movements list, pagination metadata).
        """
        logger.info(
            "listing_movements",
            page=pagination.page if pagination else 1,
            product_id=str(product_id) if product_id else None,
        )
        return self.repository.list_with_filters(
            pagination=pagination,
            product_id=product_id,
            movement_type=movement_type,
            reason=reason,
            date_from=date_from,
            date_to=date_to,
        )
