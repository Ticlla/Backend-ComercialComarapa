"""Category repository for data access.

This module provides the CategoryRepository for managing category entities.

Usage:
    from comercial_comarapa.db.repositories.category import CategoryRepository
    from comercial_comarapa.db.database import get_db

    db = get_db()
    repo = CategoryRepository(db)
    categories, pagination = repo.list()
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from comercial_comarapa.db.repositories.base import BaseRepository
from comercial_comarapa.models.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

if TYPE_CHECKING:
    from comercial_comarapa.core.protocols import DatabaseClientProtocol


class CategoryRepository(BaseRepository[CategoryResponse, CategoryCreate, CategoryUpdate]):
    """Repository for Category entities."""

    table_name = "categories"
    response_model = CategoryResponse
    entity_name = "Category"

    def __init__(self, db: DatabaseClientProtocol):
        """Initialize category repository.

        Args:
            db: Database client.
        """
        super().__init__(db)

    def get_by_name(self, name: str) -> CategoryResponse | None:
        """Get category by name.

        Args:
            name: Category name.

        Returns:
            Category if found, None otherwise.
        """
        result = (
            self.db.table(self.table_name)
            .select("*")
            .eq("name", name)
            .single()
            .execute()
        )

        if result.data:
            return self.response_model.model_validate(result.data)
        return None

    def name_exists(self, name: str, exclude_id: str | None = None) -> bool:
        """Check if a category name already exists.

        Args:
            name: Category name to check.
            exclude_id: Optional ID to exclude (for updates).

        Returns:
            True if name exists, False otherwise.
        """
        query = self.db.table(self.table_name).select("id").eq("name", name)

        if exclude_id:
            query = query.neq("id", exclude_id)

        result = query.execute()
        return len(result.data or []) > 0


