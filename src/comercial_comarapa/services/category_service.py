"""Category service for business logic.

This module provides the CategoryService class that encapsulates
all business logic related to categories.

Usage:
    from comercial_comarapa.services.category_service import CategoryService
    from comercial_comarapa.db.database import get_db

    db = get_db()
    service = CategoryService(db)
    categories, pagination = service.list_categories()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from comercial_comarapa.core.exceptions import (
    CategoryNotFoundError,
    DuplicateEntityError,
    InvalidOperationError,
)
from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.db.repositories.category import CategoryRepository

if TYPE_CHECKING:
    from uuid import UUID

    from comercial_comarapa.core.protocols import DatabaseClientProtocol
    from comercial_comarapa.models.category import (
        CategoryCreate,
        CategoryResponse,
        CategoryUpdate,
    )
    from comercial_comarapa.models.common import PaginationMeta, PaginationParams

logger = get_logger(__name__)


class CategoryService:
    """Service class for category business logic.

    Handles validation, business rules, and orchestrates
    repository operations for categories.
    """

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize category service.

        Args:
            db: Database client.
        """
        self.db = db
        self.repository = CategoryRepository(db)

    def list_categories(
        self,
        pagination: PaginationParams | None = None,
    ) -> tuple[list[CategoryResponse], PaginationMeta]:
        """List all categories with pagination.

        Args:
            pagination: Pagination parameters.

        Returns:
            Tuple of (categories list, pagination metadata).
        """
        logger.info("listing_categories", page=pagination.page if pagination else 1)
        return self.repository.list(
            pagination=pagination,
            order_by="name",
        )

    def get_category(self, category_id: UUID) -> CategoryResponse:
        """Get a category by ID.

        Args:
            category_id: Category UUID.

        Returns:
            Category if found.

        Raises:
            CategoryNotFoundError: If category not found.
        """
        logger.info("getting_category", category_id=str(category_id))
        category = self.repository.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)
        return category

    def create_category(self, data: CategoryCreate) -> CategoryResponse:
        """Create a new category.

        Args:
            data: Category creation data.

        Returns:
            Created category.

        Raises:
            DuplicateEntityError: If category name already exists.
        """
        logger.info("creating_category", name=data.name)

        # Check for duplicate name
        if self.repository.name_exists(data.name):
            raise DuplicateEntityError("Category", "name", data.name)

        category = self.repository.create(data)
        logger.info("category_created", category_id=str(category.id), name=category.name)
        return category

    def update_category(
        self,
        category_id: UUID,
        data: CategoryUpdate,
    ) -> CategoryResponse:
        """Update an existing category.

        Args:
            category_id: Category UUID.
            data: Update data.

        Returns:
            Updated category.

        Raises:
            CategoryNotFoundError: If category not found.
            DuplicateEntityError: If new name already exists.
        """
        logger.info("updating_category", category_id=str(category_id))

        # Verify category exists
        existing = self.repository.get_by_id(category_id)
        if existing is None:
            raise CategoryNotFoundError(category_id)

        # Check for duplicate name if name is being changed
        if (
            data.name
            and data.name != existing.name
            and self.repository.name_exists(data.name, exclude_id=str(category_id))
        ):
            raise DuplicateEntityError("Category", "name", data.name)

        category = self.repository.update(category_id, data)
        if category is None:
            raise CategoryNotFoundError(category_id)

        logger.info("category_updated", category_id=str(category_id))
        return category

    def delete_category(self, category_id: UUID) -> None:
        """Delete a category.

        Args:
            category_id: Category UUID.

        Raises:
            CategoryNotFoundError: If category not found.
            InvalidOperationError: If category has associated products.
        """
        logger.info("deleting_category", category_id=str(category_id))

        # Verify category exists
        if not self.repository.exists(category_id):
            raise CategoryNotFoundError(category_id)

        # Check if category has products
        if self._has_products(category_id):
            raise InvalidOperationError(
                f"Cannot delete category '{category_id}': it has associated products",
                {"category_id": str(category_id)},
            )

        self.repository.delete_or_raise(category_id)
        logger.info("category_deleted", category_id=str(category_id))

    def _has_products(self, category_id: UUID) -> bool:
        """Check if category has associated products.

        Args:
            category_id: Category UUID.

        Returns:
            True if category has products, False otherwise.
        """
        result = (
            self.db.table("products")
            .select("id")
            .eq("category_id", str(category_id))
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return len(result.data or []) > 0
