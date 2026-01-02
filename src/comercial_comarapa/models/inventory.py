"""Inventory movement models for request/response validation."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# ENUMS
# =============================================================================


class MovementType(str, Enum):
    """Type of inventory movement."""

    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ADJUSTMENT = "ADJUSTMENT"


class MovementReason(str, Enum):
    """Reason for inventory movement."""

    PURCHASE = "PURCHASE"
    SALE = "SALE"
    RETURN = "RETURN"
    DAMAGE = "DAMAGE"
    CORRECTION = "CORRECTION"
    OTHER = "OTHER"


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class StockEntryRequest(BaseModel):
    """Request to add stock (entry)."""

    product_id: UUID = Field(description="Product to add stock to")
    quantity: int = Field(gt=0, description="Quantity to add (must be positive)")
    reason: MovementReason = Field(
        default=MovementReason.PURCHASE,
        description="Reason for entry",
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes",
    )


class StockExitRequest(BaseModel):
    """Request to remove stock (exit)."""

    product_id: UUID = Field(description="Product to remove stock from")
    quantity: int = Field(gt=0, description="Quantity to remove (must be positive)")
    reason: MovementReason = Field(description="Reason for exit")
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes",
    )


class StockAdjustmentRequest(BaseModel):
    """Request to adjust stock to specific value."""

    product_id: UUID = Field(description="Product to adjust")
    new_stock: int = Field(ge=0, description="New stock level (absolute value)")
    reason: MovementReason = Field(
        default=MovementReason.CORRECTION,
        description="Reason for adjustment",
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes (recommended for adjustments)",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class MovementResponse(BaseModel):
    """Inventory movement response."""

    id: UUID = Field(description="Movement unique identifier")
    product_id: UUID = Field(description="Product ID")
    product_name: str | None = Field(default=None, description="Product name (denormalized)")
    product_sku: str | None = Field(default=None, description="Product SKU (denormalized)")
    movement_type: MovementType = Field(description="Type of movement")
    quantity: int = Field(description="Quantity moved")
    reason: MovementReason = Field(description="Reason for movement")
    reference_id: UUID | None = Field(default=None, description="Reference to sale/purchase")
    notes: str | None = Field(default=None, description="Movement notes")
    previous_stock: int = Field(description="Stock before movement")
    new_stock: int = Field(description="Stock after movement")
    created_at: datetime = Field(description="Movement timestamp")
    created_by: UUID | None = Field(default=None, description="User who created movement")

    model_config = ConfigDict(from_attributes=True)


class MovementSummary(BaseModel):
    """Summary of movements for a product."""

    product_id: UUID
    product_name: str
    total_entries: int = Field(description="Total entry movements")
    total_exits: int = Field(description="Total exit movements")
    total_adjustments: int = Field(description="Total adjustments")
    net_change: int = Field(description="Net stock change")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# FILTER SCHEMAS
# =============================================================================


class MovementFilter(BaseModel):
    """Filter parameters for movement listing."""

    product_id: UUID | None = Field(default=None, description="Filter by product")
    movement_type: MovementType | None = Field(default=None, description="Filter by type")
    reason: MovementReason | None = Field(default=None, description="Filter by reason")
    date_from: datetime | None = Field(default=None, description="Start date")
    date_to: datetime | None = Field(default=None, description="End date")
