"""Core module for shared utilities and configurations.

This module exports core components:
- exceptions: Domain exception hierarchy
- exception_handlers: FastAPI exception handlers
- protocols: Type-safe protocol definitions
- logging: Structured logging utilities
"""

from comercial_comarapa.core.exception_handlers import register_exception_handlers
from comercial_comarapa.core.exceptions import (
    BusinessRuleError,
    CategoryNotFoundError,
    ConfigurationError,
    ConnectionError,
    DatabaseError,
    DomainError,
    DuplicateEntityError,
    DuplicateSKUError,
    EntityNotFoundError,
    InsufficientStockError,
    InvalidDatabaseModeError,
    InvalidOperationError,
    ProductNotFoundError,
    SaleAlreadyCancelledError,
    SaleNotFoundError,
    TransactionError,
    UniqueConstraintViolationError,
    ValidationError,
)
from comercial_comarapa.core.logging import (
    configure_logging,
    get_logger,
    log_db_query,
    log_error,
    log_request,
)
from comercial_comarapa.core.protocols import (
    DatabaseClientProtocol,
    QueryResultProtocol,
    TableQueryProtocol,
)

__all__ = [
    "BusinessRuleError",
    "CategoryNotFoundError",
    "ConfigurationError",
    "ConnectionError",
    "DatabaseClientProtocol",
    "DatabaseError",
    "DomainError",
    "DuplicateEntityError",
    "DuplicateSKUError",
    "EntityNotFoundError",
    "InsufficientStockError",
    "InvalidDatabaseModeError",
    "InvalidOperationError",
    "ProductNotFoundError",
    "QueryResultProtocol",
    "SaleAlreadyCancelledError",
    "SaleNotFoundError",
    "TableQueryProtocol",
    "TransactionError",
    "UniqueConstraintViolationError",
    "ValidationError",
    "configure_logging",
    "get_logger",
    "log_db_query",
    "log_error",
    "log_request",
    "register_exception_handlers",
]
