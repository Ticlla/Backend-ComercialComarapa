"""Structured logging configuration using structlog.

This module provides a configured logger for consistent, structured logging
across the application.

Usage:
    from comercial_comarapa.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("user_created", user_id="123", email="user@example.com")
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

import structlog

from comercial_comarapa.config import settings

if TYPE_CHECKING:
    from structlog.types import Processor


def configure_logging() -> None:
    """Configure structlog for the application.

    Sets up processors for both development (pretty console output)
    and production (JSON output) environments.
    """
    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_development:
        # Development: pretty console output
        processors: list[Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output for log aggregation
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured structlog BoundLogger.

    Example:
        logger = get_logger(__name__)
        logger.info("operation_completed", duration_ms=42)
    """
    return structlog.get_logger(name)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """Log an HTTP request with standard fields.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional fields to log
    """
    logger = get_logger("http")
    logger.info(
        "http_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        **kwargs,
    )


def log_db_query(
    operation: str,
    table: str,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """Log a database query with standard fields.

    Args:
        operation: Query type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_ms: Query duration in milliseconds
        **kwargs: Additional fields to log
    """
    logger = get_logger("db")
    logger.debug(
        "db_query",
        operation=operation,
        table=table,
        duration_ms=round(duration_ms, 2),
        **kwargs,
    )


def log_error(
    error: Exception,
    context: str | None = None,
    **kwargs: Any,
) -> None:
    """Log an error with exception details.

    Args:
        error: The exception that occurred
        context: Context where the error occurred
        **kwargs: Additional fields to log
    """
    logger = get_logger("error")
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        exc_info=error,
        **kwargs,
    )

