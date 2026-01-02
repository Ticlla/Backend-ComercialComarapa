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

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ClassVar

from comercial_comarapa.config import settings

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

# =============================================================================
# ALLOWED TABLES AND COLUMNS (Whitelist for SQL Injection Prevention)
# =============================================================================

ALLOWED_TABLES = frozenset({
    "categories",
    "products",
    "inventory_movements",
    "sales",
    "sale_items",
})

ALLOWED_COLUMNS = frozenset({
    # Common
    "id", "created_at", "updated_at", "created_by",
    # Categories
    "name", "description",
    # Products
    "sku", "category_id", "unit_price", "cost_price",
    "current_stock", "min_stock_level", "is_active",
    # Inventory movements
    "product_id", "movement_type", "quantity", "reason",
    "reference_id", "notes", "previous_stock", "new_stock",
    # Sales
    "sale_number", "sale_date", "subtotal", "discount", "tax", "total", "status",
    # Sale items
    "sale_id",
})


def _validate_identifier(name: str, allowed: frozenset[str], kind: str) -> str:
    """Validate that an identifier is in the allowlist.

    Args:
        name: The identifier to validate.
        allowed: Set of allowed identifiers.
        kind: Type of identifier for error message (table/column).

    Returns:
        The validated identifier.

    Raises:
        ValueError: If identifier is not in allowlist.
    """
    if name not in allowed:
        raise ValueError(f"Invalid {kind} name: {name}")
    return name


def _validate_table(table_name: str) -> str:
    """Validate table name against allowlist."""
    return _validate_identifier(table_name, ALLOWED_TABLES, "table")


def _validate_columns(columns: str) -> str:
    """Validate column names against allowlist.

    Args:
        columns: Comma-separated column names or '*'.

    Returns:
        Validated columns string.

    Raises:
        ValueError: If any column is not in allowlist.
    """
    if columns == "*":
        return columns

    col_list = [c.strip() for c in columns.split(",")]
    for col in col_list:
        if col not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid column name: {col}")
    return columns


# =============================================================================
# CONNECTION POOL MANAGER (Singleton Pattern)
# =============================================================================


class PoolManager:
    """Singleton manager for the database connection pool."""

    _instance: ClassVar[PoolManager | None] = None
    _pool: ConnectionPool | None = None

    def __new__(cls) -> PoolManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_pool(self) -> ConnectionPool:
        """Get or create the connection pool.

        Returns:
            ConnectionPool instance.

        Raises:
            ImportError: If psycopg_pool is not installed.
        """
        if self._pool is None:
            from psycopg_pool import ConnectionPool  # noqa: PLC0415

            self._pool = ConnectionPool(
                conninfo=settings.database_url,
                min_size=2,
                max_size=10,
                open=True,
            )
        return self._pool

    def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None


def get_pool() -> ConnectionPool:
    """Get the connection pool singleton.

    Returns:
        ConnectionPool instance.
    """
    return PoolManager().get_pool()


def close_pool() -> None:
    """Close the connection pool."""
    PoolManager().close()


# =============================================================================
# LOCAL DATABASE CLIENT
# =============================================================================


class LocalDatabaseClient:
    """Database client for local PostgreSQL using psycopg with connection pooling.

    This client provides a simple interface for database operations
    when running with a local Docker PostgreSQL instance.
    """

    _instance: ClassVar[LocalDatabaseClient | None] = None

    def __new__(cls) -> LocalDatabaseClient:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pool_manager = PoolManager()
        return cls._instance

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool as context manager.

        Yields:
            psycopg connection object.

        Example:
            with client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        with self._pool_manager.get_pool().connection() as conn:
            yield conn

    def table(self, table_name: str) -> TableQuery:
        """Get a table query builder.

        Args:
            table_name: Name of the table to query.

        Returns:
            TableQuery instance for building queries.

        Raises:
            ValueError: If table name is not in allowlist.
        """
        _validate_table(table_name)
        return TableQuery(self, table_name)

    def close(self) -> None:
        """Close the connection pool."""
        close_pool()


# =============================================================================
# TABLE QUERY BUILDER
# =============================================================================


class TableQuery:
    """Query builder for table operations with SQL injection protection.

    Provides a Supabase-like interface for database operations.
    All identifiers are validated against allowlists.
    """

    def __init__(self, client: LocalDatabaseClient, table_name: str):
        self.client = client
        self.table_name = table_name
        self._select_cols = "*"
        self._filters: list[tuple[str, str, Any]] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._order_by: str | None = None
        self._order_desc: bool = False
        self._single = False

    def select(self, columns: str = "*") -> TableQuery:
        """Set columns to select.

        Args:
            columns: Comma-separated column names or '*'.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If any column is not in allowlist.
        """
        _validate_columns(columns)
        self._select_cols = columns
        return self

    def eq(self, column: str, value: Any) -> TableQuery:
        """Add equality filter.

        Args:
            column: Column name to filter.
            value: Value to match.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If column is not in allowlist.
        """
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "=", value))
        return self

    def neq(self, column: str, value: Any) -> TableQuery:
        """Add not-equal filter."""
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "!=", value))
        return self

    def gt(self, column: str, value: Any) -> TableQuery:
        """Add greater-than filter."""
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, ">", value))
        return self

    def gte(self, column: str, value: Any) -> TableQuery:
        """Add greater-than-or-equal filter."""
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, ">=", value))
        return self

    def lt(self, column: str, value: Any) -> TableQuery:
        """Add less-than filter."""
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "<", value))
        return self

    def lte(self, column: str, value: Any) -> TableQuery:
        """Add less-than-or-equal filter."""
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "<=", value))
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
        """Order results.

        Args:
            column: Column to order by.
            desc: If True, order descending.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If column is not in allowlist.
        """
        _validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._order_by = column
        self._order_desc = desc
        return self

    def single(self) -> TableQuery:
        """Expect single result."""
        self._single = True
        self._limit = 1
        return self

    def _build_select_query(self) -> tuple[str, list[Any]]:
        """Build SELECT query with parameters.

        Returns:
            Tuple of (query_string, parameters_list).
        """
        from psycopg import sql  # noqa: PLC0415

        # Build column selection
        if self._select_cols == "*":
            cols = sql.SQL("*")
        else:
            col_names = [c.strip() for c in self._select_cols.split(",")]
            cols = sql.SQL(", ").join(sql.Identifier(c) for c in col_names)

        # Base query
        query = sql.SQL("SELECT {} FROM {}").format(
            cols,
            sql.Identifier(self.table_name),
        )

        params: list[Any] = []

        # WHERE clause
        if self._filters:
            conditions = []
            for col, op, val in self._filters:
                conditions.append(
                    sql.SQL("{} {} %s").format(sql.Identifier(col), sql.SQL(op))
                )
                params.append(val)
            query = sql.SQL("{} WHERE {}").format(
                query, sql.SQL(" AND ").join(conditions)
            )

        # ORDER BY
        if self._order_by:
            direction = sql.SQL("DESC") if self._order_desc else sql.SQL("ASC")
            query = sql.SQL("{} ORDER BY {} {}").format(
                query, sql.Identifier(self._order_by), direction
            )

        # LIMIT
        if self._limit is not None:
            query = sql.SQL("{} LIMIT %s").format(query)
            params.append(self._limit)

        # OFFSET
        if self._offset is not None:
            query = sql.SQL("{} OFFSET %s").format(query)
            params.append(self._offset)

        return query, params

    def execute(self) -> QueryResult:
        """Execute the SELECT query.

        Returns:
            QueryResult with data.
        """
        query, params = self._build_select_query()

        with self.client.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()

                # Convert to list of dicts
                data = [dict(zip(columns, row, strict=False)) for row in rows]

                if self._single:
                    data = data[0] if data else None

                return QueryResult(data=data)
            except Exception:
                conn.rollback()
                raise

    def insert(self, data: dict) -> QueryResult:
        """Insert a record.

        Args:
            data: Dictionary of column names to values.

        Returns:
            QueryResult with inserted record.
        """
        from psycopg import sql  # noqa: PLC0415

        # Validate all column names
        for col in data:
            _validate_identifier(col, ALLOWED_COLUMNS, "column")

        columns = sql.SQL(", ").join(sql.Identifier(k) for k in data)
        placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in data)

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
            sql.Identifier(self.table_name),
            columns,
            placeholders,
        )

        with self.client.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, list(data.values()))
                    cols = [desc[0] for desc in cursor.description]
                    row = cursor.fetchone()
                    result = dict(zip(cols, row, strict=False)) if row else None
                conn.commit()
                return QueryResult(data=[result] if result else [])
            except Exception:
                conn.rollback()
                raise

    def update(self, data: dict) -> QueryResult:
        """Update records matching filters.

        Args:
            data: Dictionary of column names to new values.

        Returns:
            QueryResult with updated records.
        """
        from psycopg import sql  # noqa: PLC0415

        # Validate all column names
        for col in data:
            _validate_identifier(col, ALLOWED_COLUMNS, "column")

        set_items = sql.SQL(", ").join(
            sql.SQL("{} = %s").format(sql.Identifier(k)) for k in data
        )

        query = sql.SQL("UPDATE {} SET {}").format(
            sql.Identifier(self.table_name),
            set_items,
        )

        params = list(data.values())

        # WHERE clause
        if self._filters:
            conditions = []
            for col, op, val in self._filters:
                conditions.append(
                    sql.SQL("{} {} %s").format(sql.Identifier(col), sql.SQL(op))
                )
                params.append(val)
            query = sql.SQL("{} WHERE {}").format(
                query, sql.SQL(" AND ").join(conditions)
            )

        query = sql.SQL("{} RETURNING *").format(query)

        with self.client.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    cols = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(cols, row, strict=False)) for row in rows]
                conn.commit()
                return QueryResult(data=result)
            except Exception:
                conn.rollback()
                raise

    def delete(self) -> QueryResult:
        """Delete records matching filters.

        Returns:
            QueryResult with deleted records.
        """
        from psycopg import sql  # noqa: PLC0415

        query = sql.SQL("DELETE FROM {}").format(sql.Identifier(self.table_name))

        params: list[Any] = []

        # WHERE clause
        if self._filters:
            conditions = []
            for col, op, val in self._filters:
                conditions.append(
                    sql.SQL("{} {} %s").format(sql.Identifier(col), sql.SQL(op))
                )
                params.append(val)
            query = sql.SQL("{} WHERE {}").format(
                query, sql.SQL(" AND ").join(conditions)
            )

        query = sql.SQL("{} RETURNING *").format(query)

        with self.client.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    cols = [desc[0] for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    result = [dict(zip(cols, row, strict=False)) for row in rows]
                conn.commit()
                return QueryResult(data=result)
            except Exception:
                conn.rollback()
                raise


# =============================================================================
# QUERY RESULT
# =============================================================================


class QueryResult:
    """Result container matching Supabase response structure."""

    def __init__(self, data: Any):
        self.data = data


# =============================================================================
# DATABASE CLIENT FACTORY
# =============================================================================


def get_db_client() -> LocalDatabaseClient | Any:
    """Get database client based on configuration.

    Returns:
        LocalDatabaseClient for local mode, or Supabase Client for cloud mode.

    Raises:
        ValueError: If configuration is invalid.
    """
    if settings.is_local_db:
        return LocalDatabaseClient()
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


# =============================================================================
# HEALTH CHECK
# =============================================================================


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
