"""Base repository pattern for data access abstraction.

This module provides a generic base repository class that encapsulates
common CRUD operations and can be extended for specific entities.

Usage:
    from comercial_comarapa.db.repositories.base import BaseRepository

    class ProductRepository(BaseRepository[ProductResponse, ProductCreate, ProductUpdate]):
        table_name = "products"
        response_model = ProductResponse
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from comercial_comarapa.core.exceptions import EntityNotFoundError
from comercial_comarapa.core.logging import get_logger, log_db_query
from comercial_comarapa.models.common import PaginationMeta, PaginationParams

if TYPE_CHECKING:
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol

logger = get_logger(__name__)


class BaseRepository[T: BaseModel, C: BaseModel, U: BaseModel]:
    """Generic base repository for CRUD operations.

    This class provides common database operations that can be inherited
    by entity-specific repositories.

    Type Parameters:
        T: Response model type (e.g., ProductResponse)
        C: Create model type (e.g., ProductCreate)
        U: Update model type (e.g., ProductUpdate)

    Attributes:
        table_name: Name of the database table.
        response_model: Pydantic model class for responses.
        entity_name: Human-readable entity name for error messages.
    """

    table_name: str
    response_model: type[T]
    entity_name: str = "Entity"

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize repository with database client.

        Args:
            db: Database client conforming to DatabaseClientProtocol.
        """
        self.db = db

    def get_by_id(self, entity_id: UUID) -> T | None:
        """Get entity by ID.

        Args:
            entity_id: UUID of the entity.

        Returns:
            Entity if found, None otherwise.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        result = (
            self.db.table(self.table_name).select("*").eq("id", str(entity_id)).single().execute()
        )

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("SELECT", self.table_name, duration_ms, id=str(entity_id))

        if result.data:
            return self.response_model.model_validate(result.data)
        return None

    def get_by_id_or_raise(self, entity_id: UUID) -> T:
        """Get entity by ID or raise EntityNotFoundError.

        Args:
            entity_id: UUID of the entity.

        Returns:
            Entity if found.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(self.entity_name, entity_id)
        return entity

    def list(
        self,
        pagination: PaginationParams | None = None,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> tuple[list[T], PaginationMeta]:
        """List entities with pagination and optional filters.

        Args:
            pagination: Pagination parameters (defaults to page=1, page_size=20).
            filters: Dictionary of column-value pairs to filter by.
            order_by: Column to order by.
            order_desc: If True, order descending.

        Returns:
            Tuple of (list of entities, pagination metadata).
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        if pagination is None:
            pagination = PaginationParams()

        # Build query
        query = self.db.table(self.table_name).select("*")

        # Apply filters
        if filters:
            for column, value in filters.items():
                if value is not None:
                    query = query.eq(column, value)

        # Apply ordering
        if order_by:
            query = query.order(order_by, desc=order_desc)

        # Apply pagination
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
            page_size=pagination.page_size,
        )

        # Parse results
        entities = [self.response_model.model_validate(row) for row in result.data or []]

        # Get total count for pagination
        total_items = self._count(filters)

        pagination_meta = PaginationMeta.create(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total_items,
        )

        return entities, pagination_meta

    def _count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities matching filters using optimized COUNT(*).

        Args:
            filters: Dictionary of column-value pairs to filter by.

        Returns:
            Count of matching entities.
        """
        query = self.db.table(self.table_name).select("id")

        if filters:
            for column, value in filters.items():
                if value is not None:
                    query = query.eq(column, value)

        # Use optimized count() method instead of fetching all rows
        return query.count()

    def create(self, data: C) -> T:
        """Create a new entity.

        Args:
            data: Create model with entity data.

        Returns:
            Created entity.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        # Convert Pydantic model to dict, excluding unset values
        insert_data = data.model_dump(exclude_unset=True)

        result = self.db.table(self.table_name).insert(insert_data).data

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("INSERT", self.table_name, duration_ms)

        if result and len(result) > 0:
            return self.response_model.model_validate(result[0])

        # This shouldn't happen with RETURNING *, but handle gracefully
        raise RuntimeError(f"Failed to create {self.entity_name}")

    def update(self, entity_id: UUID, data: U) -> T | None:
        """Update an existing entity.

        Args:
            entity_id: UUID of the entity to update.
            data: Update model with fields to update.

        Returns:
            Updated entity if found, None otherwise.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        # Convert to dict, excluding unset values for partial updates
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            # Nothing to update, return current entity
            return self.get_by_id(entity_id)

        result = (self.db.table(self.table_name).eq("id", str(entity_id)).update(update_data)).data

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("UPDATE", self.table_name, duration_ms, id=str(entity_id))

        if result and len(result) > 0:
            return self.response_model.model_validate(result[0])
        return None

    def update_or_raise(self, entity_id: UUID, data: U) -> T:
        """Update an entity or raise EntityNotFoundError.

        Args:
            entity_id: UUID of the entity to update.
            data: Update model with fields to update.

        Returns:
            Updated entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        entity = self.update(entity_id, data)
        if entity is None:
            raise EntityNotFoundError(self.entity_name, entity_id)
        return entity

    def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: UUID of the entity to delete.

        Returns:
            True if entity was deleted, False if not found.
        """
        import time  # noqa: PLC0415

        start = time.perf_counter()

        result = (self.db.table(self.table_name).eq("id", str(entity_id)).delete()).data

        duration_ms = (time.perf_counter() - start) * 1000
        log_db_query("DELETE", self.table_name, duration_ms, id=str(entity_id))

        return len(result or []) > 0

    def delete_or_raise(self, entity_id: UUID) -> None:
        """Delete an entity or raise EntityNotFoundError.

        Args:
            entity_id: UUID of the entity to delete.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        if not self.delete(entity_id):
            raise EntityNotFoundError(self.entity_name, entity_id)

    def exists(self, entity_id: UUID) -> bool:
        """Check if an entity exists.

        Args:
            entity_id: UUID of the entity.

        Returns:
            True if entity exists, False otherwise.
        """
        result = (
            self.db.table(self.table_name).select("id").eq("id", str(entity_id)).single().execute()
        )
        return result.data is not None
