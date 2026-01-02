"""Unified database client supporting local PostgreSQL and Supabase.

This module provides a database client factory that returns the appropriate
client based on the DATABASE_MODE configuration.

Usage:
    from comercial_comarapa.db.database import get_db, check_db_connection

    # In FastAPI dependency
    def get_repository(db = Depends(get_db)):
        return ProductRepository(db)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from comercial_comarapa.config import settings
from comercial_comarapa.core.exceptions import InvalidDatabaseModeError

if TYPE_CHECKING:
    from comercial_comarapa.core.protocols import DatabaseClientProtocol

# Re-export for backwards compatibility
from comercial_comarapa.db.health import check_db_connection
from comercial_comarapa.db.local_client import (
    LocalDatabaseClient,
    QueryResult,
    TableQuery,
)
from comercial_comarapa.db.pool import close_pool, get_pool
from comercial_comarapa.db.whitelist import ALLOWED_COLUMNS, ALLOWED_TABLES

__all__ = [
    "ALLOWED_COLUMNS",
    "ALLOWED_TABLES",
    "LocalDatabaseClient",
    "QueryResult",
    "TableQuery",
    "check_db_connection",
    "close_pool",
    "get_db",
    "get_db_client",
    "get_pool",
]


def get_db_client() -> DatabaseClientProtocol:
    """Get database client based on configuration.

    Returns:
        Database client conforming to DatabaseClientProtocol.

    Raises:
        InvalidDatabaseModeError: If DATABASE_MODE is not 'local' or 'supabase'.
    """
    if settings.is_local_db:
        return LocalDatabaseClient()
    elif settings.is_supabase_db:
        from comercial_comarapa.db.supabase import get_supabase_client  # noqa: PLC0415

        return get_supabase_client()
    else:
        raise InvalidDatabaseModeError(settings.database_mode)


def get_db() -> DatabaseClientProtocol:
    """Dependency for FastAPI to inject database client.

    Returns:
        Database client instance.
    """
    return get_db_client()
