"""SQL injection prevention through identifier whitelisting.

This module defines allowed tables and columns for the database layer,
providing validation functions to ensure only safe identifiers are used.
"""

from __future__ import annotations

from comercial_comarapa.core.exceptions import ValidationError

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


def validate_identifier(name: str, allowed: frozenset[str], kind: str) -> str:
    """Validate that an identifier is in the allowlist.

    Args:
        name: The identifier to validate.
        allowed: Set of allowed identifiers.
        kind: Type of identifier for error message (table/column).

    Returns:
        The validated identifier.

    Raises:
        ValidationError: If identifier is not in allowlist.
    """
    if name not in allowed:
        raise ValidationError(
            f"Invalid {kind} name: {name}",
            field=kind,
            details={"name": name, "allowed": list(allowed)[:10]},  # Limit for readability
        )
    return name


def validate_table(table_name: str) -> str:
    """Validate table name against allowlist.

    Args:
        table_name: Name of the table to validate.

    Returns:
        The validated table name.

    Raises:
        ValidationError: If table is not in allowlist.
    """
    return validate_identifier(table_name, ALLOWED_TABLES, "table")


def validate_columns(columns: str) -> str:
    """Validate column names against allowlist.

    Args:
        columns: Comma-separated column names or '*'.

    Returns:
        Validated columns string.

    Raises:
        ValidationError: If any column is not in allowlist.
    """
    if columns == "*":
        return columns

    col_list = [c.strip() for c in columns.split(",")]
    for col in col_list:
        if col not in ALLOWED_COLUMNS:
            raise ValidationError(
                f"Invalid column name: {col}",
                field="column",
                details={"column": col},
            )
    return columns

