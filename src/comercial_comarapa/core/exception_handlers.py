"""FastAPI exception handlers for domain exceptions.

This module registers exception handlers that convert domain exceptions
to proper HTTP responses with consistent error format.

Usage:
    from comercial_comarapa.core.exception_handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
"""

import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from psycopg.errors import UniqueViolation
from pydantic import ValidationError as PydanticValidationError

from comercial_comarapa.core.exceptions import DomainError, UniqueConstraintViolationError
from comercial_comarapa.core.logging import get_logger

logger = get_logger(__name__)


def _parse_unique_violation(error_message: str) -> tuple[str | None, str | None]:
    """Parse PostgreSQL unique violation error message.

    Args:
        error_message: The error message from psycopg.

    Returns:
        Tuple of (constraint_name, field_name) if parseable, else (None, None).
    """
    # Pattern: duplicate key value violates unique constraint "categories_name_key"
    constraint_match = re.search(r'unique constraint "(\w+)"', error_message)
    constraint_name = constraint_match.group(1) if constraint_match else None

    # Try to extract field name from constraint name (e.g., categories_name_key -> name)
    field_name = None
    if constraint_name:
        # Common patterns: tablename_fieldname_key, tablename_fieldname_idx
        parts = constraint_name.replace("_key", "").replace("_idx", "").split("_")
        if len(parts) >= 2:
            field_name = parts[-1]  # Last part is usually the field name

    return constraint_name, field_name


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        _request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        """Handle all domain exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.to_dict(),
            },
        )

    @app.exception_handler(UniqueViolation)
    async def unique_violation_handler(
        _request: Request,
        exc: UniqueViolation,
    ) -> JSONResponse:
        """Handle PostgreSQL unique constraint violations.

        Converts database-level UniqueViolation to a user-friendly 409 response.
        """
        error_message = str(exc)
        constraint_name, field_name = _parse_unique_violation(error_message)

        logger.warning(
            "unique_constraint_violation",
            constraint=constraint_name,
            field=field_name,
            error=error_message,
        )

        # Create user-friendly message
        if field_name:
            message = f"A record with this {field_name} already exists"
        else:
            message = "A record with this value already exists"

        domain_exc = UniqueConstraintViolationError(
            message=message,
            constraint_name=constraint_name,
            details={"field": field_name} if field_name else None,
        )

        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": domain_exc.to_dict(),
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_handler(
        _request: Request,
        exc: PydanticValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": errors,
                },
            },
        )
