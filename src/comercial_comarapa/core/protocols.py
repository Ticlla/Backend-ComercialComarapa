"""Protocol definitions for type-safe abstractions.

This module defines Protocol classes (structural subtyping) that allow
type-safe abstractions without requiring inheritance.

Usage:
    from comercial_comarapa.core.protocols import DatabaseClientProtocol

    def get_products(db: DatabaseClientProtocol) -> list[Product]:
        result = db.table("products").select("*").execute()
        return result.data
"""

from typing import Any, Protocol, Self


class QueryResultProtocol(Protocol):
    """Protocol for database query results."""

    @property
    def data(self) -> Any:
        """The result data from the query."""
        ...


class TableQueryProtocol(Protocol):
    """Protocol for table query builders.

    Defines the interface for building and executing database queries.
    Both LocalDatabaseClient's TableQuery and Supabase's query builder
    should conform to this protocol.
    """

    def select(self, columns: str = "*") -> Self:
        """Select specific columns.

        Args:
            columns: Comma-separated column names or '*' for all.

        Returns:
            Self for method chaining.
        """
        ...

    def eq(self, column: str, value: Any) -> Self:
        """Filter by equality.

        Args:
            column: Column name to filter.
            value: Value to match.

        Returns:
            Self for method chaining.
        """
        ...

    def neq(self, column: str, value: Any) -> Self:
        """Filter by not-equal."""
        ...

    def gt(self, column: str, value: Any) -> Self:
        """Filter by greater-than."""
        ...

    def gte(self, column: str, value: Any) -> Self:
        """Filter by greater-than-or-equal."""
        ...

    def lt(self, column: str, value: Any) -> Self:
        """Filter by less-than."""
        ...

    def lte(self, column: str, value: Any) -> Self:
        """Filter by less-than-or-equal."""
        ...

    def limit(self, count: int) -> Self:
        """Limit number of results.

        Args:
            count: Maximum number of results.

        Returns:
            Self for method chaining.
        """
        ...

    def range(self, start: int, end: int) -> Self:
        """Set range for pagination.

        Args:
            start: Starting index (0-based).
            end: Ending index (inclusive).

        Returns:
            Self for method chaining.
        """
        ...

    def order(self, column: str, desc: bool = False) -> Self:
        """Order results by column.

        Args:
            column: Column to order by.
            desc: If True, order descending.

        Returns:
            Self for method chaining.
        """
        ...

    def single(self) -> Self:
        """Expect a single result.

        Returns:
            Self for method chaining.
        """
        ...

    def execute(self) -> QueryResultProtocol:
        """Execute SELECT query.

        Returns:
            Query result with data.
        """
        ...

    def count(self) -> int:
        """Execute COUNT(*) query with current filters.

        Returns:
            Total count of matching records.
        """
        ...

    def insert(self, data: dict[str, Any]) -> QueryResultProtocol:
        """Insert a record.

        Args:
            data: Column-value pairs to insert.

        Returns:
            Query result with inserted record.
        """
        ...

    def update(self, data: dict[str, Any]) -> QueryResultProtocol:
        """Update records matching filters.

        Args:
            data: Column-value pairs to update.

        Returns:
            Query result with updated records.
        """
        ...

    def delete(self) -> QueryResultProtocol:
        """Delete records matching filters.

        Returns:
            Query result with deleted records.
        """
        ...


class DatabaseClientProtocol(Protocol):
    """Protocol for database clients.

    Both LocalDatabaseClient and Supabase Client should conform to this.
    """

    def table(self, name: str) -> TableQueryProtocol:
        """Get a table query builder.

        Args:
            name: Name of the table to query.

        Returns:
            Query builder for the specified table.
        """
        ...

    def close(self) -> None:
        """Close database connection/pool."""
        ...

