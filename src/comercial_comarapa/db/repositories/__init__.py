"""Repository pattern implementations for data access.

This module exports repository classes that abstract database operations.

Usage:
    from comercial_comarapa.db.repositories import CategoryRepository, ProductRepository
"""

from comercial_comarapa.db.repositories.base import BaseRepository
from comercial_comarapa.db.repositories.category import CategoryRepository
from comercial_comarapa.db.repositories.product import ProductRepository

__all__ = [
    "BaseRepository",
    "CategoryRepository",
    "ProductRepository",
]
