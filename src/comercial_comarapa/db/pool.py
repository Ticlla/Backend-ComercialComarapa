"""Database connection pool management.

This module provides a singleton connection pool manager for PostgreSQL
using psycopg_pool.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from comercial_comarapa.config import settings

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool


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
