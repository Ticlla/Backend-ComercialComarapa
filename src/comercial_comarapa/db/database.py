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

from functools import lru_cache
from typing import Any

from comercial_comarapa.config import settings


class LocalDatabaseClient:
    """Database client for local PostgreSQL using psycopg.

    This client provides a simple interface for database operations
    when running with a local Docker PostgreSQL instance.
    """

    def __init__(self, connection_url: str):
        """Initialize local database client.

        Args:
            connection_url: PostgreSQL connection string.
        """
        self.connection_url = connection_url
        self._connection = None

    def table(self, table_name: str) -> TableQuery:
        """Get a table query builder.

        Args:
            table_name: Name of the table to query.

        Returns:
            TableQuery instance for building queries.
        """
        return TableQuery(self, table_name)

    def get_connection(self):
        """Get or create database connection.

        Returns:
            psycopg connection object.
        """
        if self._connection is None:
            try:
                import psycopg  # noqa: PLC0415

                self._connection = psycopg.connect(self.connection_url)
            except ImportError as err:
                raise ImportError(
                    "psycopg is required for local database mode. "
                    "Install it with: pip install psycopg[binary]"
                ) from err
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


class TableQuery:
    """Simple query builder for table operations.

    Provides a Supabase-like interface for database operations.
    """

    def __init__(self, client: LocalDatabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self._select_cols = "*"
        self._filters: list[tuple[str, str, Any]] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._order_by: str | None = None
        self._single = False

    def select(self, columns: str = "*") -> TableQuery:
        """Set columns to select."""
        self._select_cols = columns
        return self

    def eq(self, column: str, value: Any) -> TableQuery:
        """Add equality filter."""
        self._filters.append((column, "=", value))
        return self

    def limit(self, count: int) -> TableQuery:
        """Limit results."""
        self._limit = count
        return self

    def range(self, start: int, end: int) -> TableQuery:
        """Set range for pagination."""
        self._offset = start
        self._limit = end - start + 1
        return self

    def order(self, column: str, desc: bool = False) -> TableQuery:
        """Order results."""
        self._order_by = f"{column} {'DESC' if desc else 'ASC'}"
        return self

    def single(self) -> TableQuery:
        """Expect single result."""
        self._single = True
        self._limit = 1
        return self

    def execute(self) -> QueryResult:
        """Execute the query."""
        conn = self.client.get_connection()
        cursor = conn.cursor()

        # Build query
        query = f"SELECT {self._select_cols} FROM {self.table_name}"

        params = []
        if self._filters:
            conditions = []
            for col, op, val in self._filters:
                conditions.append(f"{col} {op} %s")
                params.append(val)
            query += " WHERE " + " AND ".join(conditions)

        if self._order_by:
            query += f" ORDER BY {self._order_by}"

        if self._limit:
            query += f" LIMIT {self._limit}"

        if self._offset:
            query += f" OFFSET {self._offset}"

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()

        # Convert to list of dicts
        data = [dict(zip(columns, row)) for row in rows]

        if self._single:
            data = data[0] if data else None

        return QueryResult(data=data)

    def insert(self, data: dict) -> QueryResult:
        """Insert a record."""
        conn = self.client.get_connection()
        cursor = conn.cursor()

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) RETURNING *"

        cursor.execute(query, list(data.values()))
        conn.commit()

        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        result = dict(zip(columns, row)) if row else None

        return QueryResult(data=[result] if result else [])

    def update(self, data: dict) -> QueryResult:
        """Update records."""
        conn = self.client.get_connection()
        cursor = conn.cursor()

        set_clause = ", ".join([f"{k} = %s" for k in data])
        query = f"UPDATE {self.table_name} SET {set_clause}"

        params = list(data.values())

        if self._filters:
            conditions = []
            for col, op, val in self._filters:
                conditions.append(f"{col} {op} %s")
                params.append(val)
            query += " WHERE " + " AND ".join(conditions)

        query += " RETURNING *"

        cursor.execute(query, params)
        conn.commit()

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]

        return QueryResult(data=result)

    def delete(self) -> QueryResult:
        """Delete records."""
        conn = self.client.get_connection()
        cursor = conn.cursor()

        query = f"DELETE FROM {self.table_name}"

        params = []
        if self._filters:
            conditions = []
            for col, op, val in self._filters:
                conditions.append(f"{col} {op} %s")
                params.append(val)
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        conn.commit()

        return QueryResult(data=[])


class QueryResult:
    """Result container matching Supabase response structure."""

    def __init__(self, data: Any):
        self.data = data


@lru_cache
def get_db_client() -> LocalDatabaseClient | Any:
    """Get cached database client based on configuration.

    Returns:
        LocalDatabaseClient for local mode, or Supabase Client for cloud mode.

    Raises:
        ValueError: If configuration is invalid.
    """
    if settings.is_local_db:
        return LocalDatabaseClient(settings.database_url)
    elif settings.is_supabase_db:
        from comercial_comarapa.db.supabase import get_supabase_client  # noqa: PLC0415

        return get_supabase_client()
    else:
        raise ValueError(
            f"Invalid DATABASE_MODE: {settings.database_mode}. "
            "Must be 'local' or 'supabase'."
        )


def get_db() -> LocalDatabaseClient | Any:
    """Dependency for FastAPI to inject database client.

    Returns:
        Database client instance.
    """
    return get_db_client()


async def check_db_connection() -> dict:
    """Check if database connection is working.

    Returns:
        Dictionary with connection status and details.
    """
    try:
        if settings.is_local_db:
            client = get_db_client()
            # Try a simple query to verify connection
            client.table("categories").select("id").limit(1).execute()
            return {
                "status": "connected",
                "mode": "local",
                "message": "Local PostgreSQL connection successful",
            }
        elif settings.is_supabase_db:
            from comercial_comarapa.db.supabase import (  # noqa: PLC0415
                check_supabase_connection,
            )

            return await check_supabase_connection()
        else:
            return {
                "status": "error",
                "message": f"Invalid DATABASE_MODE: {settings.database_mode}",
            }
    except Exception as e:
        error_msg = str(e)
        # Check if it's just a missing table (OK during initial setup)
        if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
            return {
                "status": "connected",
                "mode": settings.database_mode,
                "message": "Database connected (tables not yet created)",
            }
        return {
            "status": "error",
            "mode": settings.database_mode,
            "message": f"Database connection failed: {error_msg}",
        }

