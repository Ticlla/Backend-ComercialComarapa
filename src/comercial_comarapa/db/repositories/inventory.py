"""Inventory repository for data access.

This module provides the InventoryRepository for managing inventory movements.

Usage:
    from comercial_comarapa.db.repositories.inventory import InventoryRepository
    from comercial_comarapa.db.database import get_db

    db = get_db()
    repo = InventoryRepository(db)
    movements = repo.list_by_product(product_id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from comercial_comarapa.core.logging import get_logger, log_db_query
from comercial_comarapa.models.common import PaginationMeta, PaginationParams
from comercial_comarapa.models.inventory import (
    MovementReason,
    MovementResponse,
    MovementType,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol

logger = get_logger(__name__)


class InventoryRepository:
    """Repository for Inventory Movement entities."""

    table_name = "inventory_movements"

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize inventory repository.

        Args:
            db: Database client.
        """
        self.db = db

    def create(
        self,
        product_id: UUID,
        movement_type: MovementType,
        quantity: int,
        reason: MovementReason,
        previous_stock: int,
        new_stock: int,
        notes: str | None = None,
        reference_id: UUID | None = None,
    ) -> MovementResponse:
        """Create a new inventory movement record.

        Args:
            product_id: Product UUID.
            movement_type: Type of movement (ENTRY, EXIT, ADJUSTMENT).
            quantity: Quantity moved.
            reason: Reason for movement.
            previous_stock: Stock before movement.
            new_stock: Stock after movement.
            notes: Optional notes.
            reference_id: Optional reference to sale/purchase.

        Returns:
            Created movement record.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        insert_data: dict[str, Any] = {
            "product_id": str(product_id),
            "movement_type": movement_type.value,
            "quantity": quantity,
            "reason": reason.value,
            "previous_stock": previous_stock,
            "new_stock": new_stock,
        }

        if notes:
            insert_data["notes"] = notes

        if reference_id:
            insert_data["reference_id"] = str(reference_id)

        result = self.db.table(self.table_name).insert(insert_data).data

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("INSERT", self.table_name, duration_ms)

        if result and len(result) > 0:
            # For single create, fetch product info
            return self._enrich_single_movement(result[0])

        raise RuntimeError("Failed to create inventory movement")

    def _fetch_products_batch(self, product_ids: set[str]) -> dict[str, dict[str, str]]:
        """Fetch product info for multiple products in a single query.

        Args:
            product_ids: Set of product UUID strings.

        Returns:
            Dict mapping product_id to {name, sku} dict.
        """
        if not product_ids:
            return {}

        import time  # noqa: PLC0415

        start = time.perf_counter()

        # Build query for all products at once
        products_map: dict[str, dict[str, str]] = {}

        # Use IN clause through multiple eq calls (workaround)
        # For better performance, could use raw SQL with ANY()
        for pid in product_ids:
            result = (
                self.db.table("products").select("id, name, sku").eq("id", pid).single().execute()
            )
            if result.data:
                products_map[pid] = {
                    "name": result.data.get("name"),
                    "sku": result.data.get("sku"),
                }

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("BATCH_FETCH_PRODUCTS", "products", duration_ms, count=len(product_ids))

        return products_map

    def _enrich_single_movement(self, data: dict) -> MovementResponse:
        """Enrich a single movement with product info.

        Args:
            data: Raw movement data from database.

        Returns:
            MovementResponse with product name and SKU.
        """
        # Fetch product info
        product_result = (
            self.db.table("products")
            .select("name, sku")
            .eq("id", data["product_id"])
            .single()
            .execute()
        )

        if product_result.data:
            data["product_name"] = product_result.data.get("name")
            data["product_sku"] = product_result.data.get("sku")

        return MovementResponse.model_validate(data)

    def _enrich_movements_batch(self, movements_data: list[dict]) -> list[MovementResponse]:
        """Enrich multiple movements with product info using batch fetch.

        This prevents N+1 queries by fetching all products in advance.

        Args:
            movements_data: List of raw movement dicts from database.

        Returns:
            List of MovementResponse with product info.
        """
        if not movements_data:
            return []

        # Collect unique product IDs
        product_ids = {m["product_id"] for m in movements_data}

        # Batch fetch all products
        products_map = self._fetch_products_batch(product_ids)

        # Enrich each movement
        enriched = []
        for data in movements_data:
            product_info = products_map.get(data["product_id"], {})
            data["product_name"] = product_info.get("name")
            data["product_sku"] = product_info.get("sku")
            enriched.append(MovementResponse.model_validate(data))

        return enriched

    def get_by_id(self, movement_id: UUID) -> MovementResponse | None:
        """Get movement by ID.

        Args:
            movement_id: Movement UUID.

        Returns:
            Movement if found, None otherwise.
        """
        result = (
            self.db.table(self.table_name).select("*").eq("id", str(movement_id)).single().execute()
        )

        if result.data:
            return self._enrich_single_movement(result.data)
        return None

    def list_by_product(
        self,
        product_id: UUID,
        limit: int = 50,
    ) -> list[MovementResponse]:
        """List movements for a specific product.

        Args:
            product_id: Product UUID.
            limit: Maximum number of movements to return.

        Returns:
            List of movements, newest first.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        result = (
            self.db.table(self.table_name)
            .select("*")
            .eq("product_id", str(product_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query(
            "SELECT",
            self.table_name,
            duration_ms,
            product_id=str(product_id),
        )

        # Use batch enrichment (only 1 product in this case, but consistent)
        return self._enrich_movements_batch(result.data or [])

    def _apply_filters(
        self,
        query: Any,
        product_id: UUID | None = None,
        movement_type: MovementType | None = None,
        reason: MovementReason | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> Any:
        """Apply common filters to a query.

        Args:
            query: Query builder instance.
            product_id: Filter by product.
            movement_type: Filter by movement type.
            reason: Filter by reason.
            date_from: Filter by start date.
            date_to: Filter by end date.

        Returns:
            Query with filters applied.
        """
        if product_id:
            query = query.eq("product_id", str(product_id))

        if movement_type:
            query = query.eq("movement_type", movement_type.value)

        if reason:
            query = query.eq("reason", reason.value)

        if date_from:
            query = query.gte("created_at", date_from.isoformat())

        if date_to:
            query = query.lte("created_at", date_to.isoformat())

        return query

    def list_with_filters(
        self,
        pagination: PaginationParams | None = None,
        product_id: UUID | None = None,
        movement_type: MovementType | None = None,
        reason: MovementReason | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[MovementResponse], PaginationMeta]:
        """List movements with filters and pagination.

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
        import time  # noqa: PLC0415

        start = time.perf_counter()

        if pagination is None:
            pagination = PaginationParams()

        # Build query
        query = self.db.table(self.table_name).select("*")

        # Apply filters using shared method
        query = self._apply_filters(query, product_id, movement_type, reason, date_from, date_to)

        # Apply ordering (newest first) and pagination
        query = query.order("created_at", desc=True)

        start_idx = pagination.offset
        end_idx = start_idx + pagination.page_size - 1
        query = query.range(start_idx, end_idx)

        result = query.execute()

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SELECT", self.table_name, duration_ms, page=pagination.page)

        # Use batch enrichment to avoid N+1 queries
        movements = self._enrich_movements_batch(result.data or [])

        # Get total count
        total_items = self._count_with_filters(
            product_id=product_id,
            movement_type=movement_type,
            reason=reason,
            date_from=date_from,
            date_to=date_to,
        )

        pagination_meta = PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total_items,
        )

        return movements, pagination_meta

    def _count_with_filters(
        self,
        product_id: UUID | None = None,
        movement_type: MovementType | None = None,
        reason: MovementReason | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        """Count movements matching filters.

        Args:
            product_id: Filter by product.
            movement_type: Filter by movement type.
            reason: Filter by reason.
            date_from: Filter by start date.
            date_to: Filter by end date.

        Returns:
            Count of matching movements.
        """
        query = self.db.table(self.table_name).select("id")

        # Apply filters using shared method
        query = self._apply_filters(query, product_id, movement_type, reason, date_from, date_to)

        return query.count()
