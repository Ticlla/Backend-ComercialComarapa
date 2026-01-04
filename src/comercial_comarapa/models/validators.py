"""Shared validators for Pydantic models.

This module provides reusable validators that can be used across
multiple Pydantic models to ensure consistent validation logic.

Usage:
    from comercial_comarapa.models.validators import decimal_validator

    class MyModel(BaseModel):
        price: Decimal

        @field_validator("price", mode="before")
        @classmethod
        def validate_price(cls, v):
            return decimal_validator(v)
"""

from decimal import Decimal, InvalidOperation
from typing import Any


def decimal_validator(value: float | str | Decimal | None) -> Decimal | None:
    """Convert value to Decimal, handling various input types.

    Args:
        value: Value to convert (float, str, Decimal, or None).

    Returns:
        Decimal if value is not None, None otherwise.

    Raises:
        ValueError: If value cannot be converted to Decimal.

    Examples:
        >>> decimal_validator(15.50)
        Decimal('15.50')
        >>> decimal_validator("10.99")
        Decimal('10.99')
        >>> decimal_validator(None)
        None
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Cannot convert '{value}' to Decimal") from e


def decimal_validator_required(value: float | str | Decimal) -> Decimal:
    """Convert value to Decimal (required, not nullable).

    Args:
        value: Value to convert (float, str, or Decimal).

    Returns:
        Decimal value.

    Raises:
        ValueError: If value is None or cannot be converted.
    """
    if value is None:
        raise ValueError("Value is required")
    return decimal_validator(value)  # type: ignore[return-value]


def positive_int_validator(value: Any) -> int:
    """Validate and convert to positive integer.

    Args:
        value: Value to validate.

    Returns:
        Positive integer.

    Raises:
        ValueError: If value is not a positive integer.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"'{value}' is not a valid integer") from e

    if int_value <= 0:
        raise ValueError(f"Value must be positive, got {int_value}")
    return int_value


def non_negative_int_validator(value: Any) -> int:
    """Validate and convert to non-negative integer.

    Args:
        value: Value to validate.

    Returns:
        Non-negative integer.

    Raises:
        ValueError: If value is negative.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"'{value}' is not a valid integer") from e

    if int_value < 0:
        raise ValueError(f"Value must be non-negative, got {int_value}")
    return int_value


def strip_string_validator(value: str | None) -> str | None:
    """Strip whitespace from string value.

    Args:
        value: String to strip, or None.

    Returns:
        Stripped string or None.
    """
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def uppercase_string_validator(value: str | None) -> str | None:
    """Convert string to uppercase.

    Args:
        value: String to convert, or None.

    Returns:
        Uppercase string or None.
    """
    if value is None:
        return None
    return value.upper()
