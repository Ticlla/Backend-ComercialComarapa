"""FastAPI dependencies for v1 API.

This module provides dependency injection functions for services
and other components used in API endpoints.

Usage:
    from comercial_comarapa.api.v1.deps import get_category_service

    @router.get("/categories")
    async def list_categories(
        service: Annotated[CategoryService, Depends(get_category_service)]
    ):
        ...
"""

from comercial_comarapa.db.database import get_db
from comercial_comarapa.services.category_service import CategoryService
from comercial_comarapa.services.inventory_service import InventoryService
from comercial_comarapa.services.product_service import ProductService


def get_category_service() -> CategoryService:
    """Get CategoryService instance with database dependency.

    Returns:
        CategoryService instance.
    """
    db = get_db()
    return CategoryService(db)


def get_product_service() -> ProductService:
    """Get ProductService instance with database dependency.

    Returns:
        ProductService instance.
    """
    db = get_db()
    return ProductService(db)


def get_inventory_service() -> InventoryService:
    """Get InventoryService instance with database dependency.

    Returns:
        InventoryService instance.
    """
    db = get_db()
    return InventoryService(db)

