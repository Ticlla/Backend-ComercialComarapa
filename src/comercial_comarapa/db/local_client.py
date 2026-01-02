"""Local PostgreSQL database client with query builder.

This module provides a database client for local PostgreSQL using psycopg
with connection pooling, along with a Supabase-like query builder interface.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ClassVar

from comercial_comarapa.core.exceptions import DatabaseError, TransactionError
from comercial_comarapa.db.pool import PoolManager, close_pool
from comercial_comarapa.db.whitelist import (
    ALLOWED_COLUMNS,
    validate_columns,
    validate_identifier,
    validate_table,
)

if TYPE_CHECKING:
    from collections.abc import Generator


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
    def get_connection(self) -> Generator[Any, None, None]:
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
            ValidationError: If table name is not in allowlist.
        """
        validate_table(table_name)
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
            ValidationError: If any column is not in allowlist.
        """
        validate_columns(columns)
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
            ValidationError: If column is not in allowlist.
        """
        validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "=", value))
        return self

    def neq(self, column: str, value: Any) -> TableQuery:
        """Add not-equal filter."""
        validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "!=", value))
        return self

    def gt(self, column: str, value: Any) -> TableQuery:
        """Add greater-than filter."""
        validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, ">", value))
        return self

    def gte(self, column: str, value: Any) -> TableQuery:
        """Add greater-than-or-equal filter."""
        validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, ">=", value))
        return self

    def lt(self, column: str, value: Any) -> TableQuery:
        """Add less-than filter."""
        validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._filters.append((column, "<", value))
        return self

    def lte(self, column: str, value: Any) -> TableQuery:
        """Add less-than-or-equal filter."""
        validate_identifier(column, ALLOWED_COLUMNS, "column")
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
            ValidationError: If column is not in allowlist.
        """
        validate_identifier(column, ALLOWED_COLUMNS, "column")
        self._order_by = column
        self._order_desc = desc
        return self

    def single(self) -> TableQuery:
        """Expect single result."""
        self._single = True
        self._limit = 1
        return self

    def _build_select_query(self) -> tuple[Any, list[Any]]:
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

        Raises:
            DatabaseError: If query execution fails.
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
            except Exception as e:
                conn.rollback()
                raise DatabaseError(
                    f"Query execution failed: {e}",
                    {"table": self.table_name, "operation": "SELECT"},
                ) from e

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
            validate_identifier(col, ALLOWED_COLUMNS, "column")

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
            except Exception as e:
                conn.rollback()
                raise TransactionError(
                    f"Insert failed: {e}",
                    {"table": self.table_name, "operation": "INSERT"},
                ) from e

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
            validate_identifier(col, ALLOWED_COLUMNS, "column")

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
            except Exception as e:
                conn.rollback()
                raise TransactionError(
                    f"Update failed: {e}",
                    {"table": self.table_name, "operation": "UPDATE"},
                ) from e

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
            except Exception as e:
                conn.rollback()
                raise TransactionError(
                    f"Delete failed: {e}",
                    {"table": self.table_name, "operation": "DELETE"},
                ) from e


# =============================================================================
# QUERY RESULT
# =============================================================================


class QueryResult:
    """Result container matching Supabase response structure."""

    def __init__(self, data: Any):
        self.data = data

