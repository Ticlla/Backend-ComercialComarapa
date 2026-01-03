"""Service layer for business logic.

This module exports service classes that encapsulate business logic
and orchestrate repository operations.
"""

from comercial_comarapa.services.category_service import CategoryService
from comercial_comarapa.services.product_service import ProductService

__all__ = [
    "CategoryService",
    "ProductService",
]
