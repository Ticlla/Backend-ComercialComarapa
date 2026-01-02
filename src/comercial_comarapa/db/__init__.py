"""Database layer - Supabase client and repositories.

This package provides database connectivity for both local PostgreSQL
and Supabase backends.

Main exports:
    - get_db: FastAPI dependency for database client injection
    - get_db_client: Get database client based on configuration
    - check_db_connection: Health check for database connectivity
    - LocalDatabaseClient: Client for local PostgreSQL
    - TableQuery: Query builder with Supabase-like API
    - QueryResult: Result container
    - ALLOWED_TABLES: Whitelist of valid table names
    - ALLOWED_COLUMNS: Whitelist of valid column names
"""

from comercial_comarapa.db.database import (
    ALLOWED_COLUMNS,
    ALLOWED_TABLES,
    LocalDatabaseClient,
    QueryResult,
    TableQuery,
    check_db_connection,
    close_pool,
    get_db,
    get_db_client,
    get_pool,
)

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
