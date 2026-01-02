"""Domain exceptions for the application.

This module defines a hierarchy of exceptions for consistent error handling
across the application. All exceptions include an error code for client handling.

Usage:
    from comercial_comarapa.core.exceptions import EntityNotFoundError

    raise EntityNotFoundError("Product", product_id)
"""

from typing import Any
from uuid import UUID


class DomainError(Exception):
    """Base exception for all domain errors.

    Attributes:
        code: Machine-readable error code for client handling.
        status_code: HTTP status code to return.
        message: Human-readable error message.
        details: Additional error context.
    """

    code: str = "DOMAIN_ERROR"
    status_code: int = 400

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details if self.details else None,
        }


# =============================================================================
# NOT FOUND ERRORS (404)
# =============================================================================


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""

    code = "ENTITY_NOT_FOUND"
    status_code = 404

    def __init__(
        self,
        entity_type: str,
        entity_id: UUID | str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id

        if entity_id:
            message = f"{entity_type} with id '{entity_id}' not found"
        else:
            message = f"{entity_type} not found"

        super().__init__(message, details)


class ProductNotFoundError(EntityNotFoundError):
    """Raised when a product does not exist."""

    code = "PRODUCT_NOT_FOUND"

    def __init__(self, product_id: UUID | str):
        super().__init__("Product", product_id)


class CategoryNotFoundError(EntityNotFoundError):
    """Raised when a category does not exist."""

    code = "CATEGORY_NOT_FOUND"

    def __init__(self, category_id: UUID | str):
        super().__init__("Category", category_id)


class SaleNotFoundError(EntityNotFoundError):
    """Raised when a sale does not exist."""

    code = "SALE_NOT_FOUND"

    def __init__(self, sale_id: UUID | str):
        super().__init__("Sale", sale_id)


# =============================================================================
# VALIDATION ERRORS (422)
# =============================================================================


class ValidationError(DomainError):
    """Raised when input validation fails."""

    code = "VALIDATION_ERROR"
    status_code = 422

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.field = field
        if field and not details:
            details = {"field": field}
        super().__init__(message, details)


class DuplicateEntityError(ValidationError):
    """Raised when attempting to create a duplicate entity."""

    code = "DUPLICATE_ENTITY"
    status_code = 409

    def __init__(
        self,
        entity_type: str,
        field: str,
        value: str,
    ):
        message = f"{entity_type} with {field} '{value}' already exists"
        super().__init__(message, field, {"field": field, "value": value})


class DuplicateSKUError(DuplicateEntityError):
    """Raised when a product SKU already exists."""

    code = "DUPLICATE_SKU"

    def __init__(self, sku: str):
        super().__init__("Product", "sku", sku)


# =============================================================================
# BUSINESS LOGIC ERRORS (400)
# =============================================================================


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""

    code = "BUSINESS_RULE_VIOLATION"
    status_code = 400


class InsufficientStockError(BusinessRuleError):
    """Raised when there's not enough stock for an operation."""

    code = "INSUFFICIENT_STOCK"

    def __init__(
        self,
        product_id: UUID | str,
        requested: int,
        available: int,
    ):
        message = f"Insufficient stock: requested {requested}, available {available}"
        super().__init__(
            message,
            {
                "product_id": str(product_id),
                "requested": requested,
                "available": available,
            },
        )


class InvalidOperationError(BusinessRuleError):
    """Raised when an operation is not allowed in current state."""

    code = "INVALID_OPERATION"


class SaleAlreadyCancelledError(InvalidOperationError):
    """Raised when trying to cancel an already cancelled sale."""

    code = "SALE_ALREADY_CANCELLED"

    def __init__(self, sale_id: UUID | str):
        super().__init__(
            f"Sale '{sale_id}' is already cancelled",
            {"sale_id": str(sale_id)},
        )


# =============================================================================
# DATABASE ERRORS (500)
# =============================================================================


class DatabaseError(DomainError):
    """Raised when a database operation fails."""

    code = "DATABASE_ERROR"
    status_code = 500

    def __init__(
        self,
        message: str = "A database error occurred",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)


class UniqueConstraintViolationError(DomainError):
    """Raised when a unique constraint is violated in the database.

    This maps PostgreSQL UniqueViolation errors to a user-friendly response.
    """

    code = "UNIQUE_CONSTRAINT_VIOLATION"
    status_code = 409

    def __init__(
        self,
        message: str = "A record with this value already exists",
        constraint_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        if constraint_name and not details:
            details = {"constraint": constraint_name}
        super().__init__(message, details)


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    code = "CONNECTION_ERROR"

    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(message)


class TransactionError(DatabaseError):
    """Raised when a database transaction fails."""

    code = "TRANSACTION_ERROR"


# =============================================================================
# CONFIGURATION ERRORS (500)
# =============================================================================


class ConfigurationError(DomainError):
    """Raised when configuration is invalid."""

    code = "CONFIGURATION_ERROR"
    status_code = 500


class InvalidDatabaseModeError(ConfigurationError):
    """Raised when DATABASE_MODE is invalid."""

    code = "INVALID_DATABASE_MODE"

    def __init__(self, mode: str):
        super().__init__(
            f"Invalid DATABASE_MODE: '{mode}'. Must be 'local' or 'supabase'.",
            {"mode": mode, "valid_modes": ["local", "supabase"]},
        )

