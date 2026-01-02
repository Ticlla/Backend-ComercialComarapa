"""Sale models for request/response validation."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# =============================================================================
# ENUMS
# =============================================================================


class SaleStatus(str, Enum):
    """Status of a sale."""

    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# =============================================================================
# SALE ITEM SCHEMAS
# =============================================================================


class SaleItemCreate(BaseModel):
    """Schema for creating a sale item."""

    product_id: UUID = Field(description="Product ID")
    quantity: int = Field(gt=0, description="Quantity to sell (must be positive)")
    unit_price: Decimal | None = Field(
        default=None,
        ge=0,
        description="Override unit price (uses product price if not provided)",
    )
    discount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Discount for this item",
    )

    @field_validator("unit_price", "discount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | str | Decimal | None) -> Decimal | None:
        """Convert price values to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))


class SaleItemResponse(BaseModel):
    """Schema for sale item in responses."""

    id: UUID = Field(description="Sale item unique identifier")
    product_id: UUID = Field(description="Product ID")
    product_name: str | None = Field(default=None, description="Product name")
    product_sku: str | None = Field(default=None, description="Product SKU")
    quantity: int = Field(description="Quantity sold")
    unit_price: Decimal = Field(description="Unit price at time of sale")
    discount: Decimal = Field(description="Discount applied")
    subtotal: Decimal = Field(description="Line subtotal (qty * price - discount)")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SALE REQUEST SCHEMAS
# =============================================================================


class SaleCreate(BaseModel):
    """Schema for creating a new sale."""

    items: list[SaleItemCreate] = Field(
        min_length=1,
        description="Sale items (at least one required)",
    )
    discount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Total sale discount",
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Sale notes",
    )

    @field_validator("discount", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | str | Decimal | None) -> Decimal:
        """Convert discount to Decimal."""
        if v is None:
            return Decimal("0")
        return Decimal(str(v))

    @model_validator(mode="after")
    def validate_items(self) -> "SaleCreate":
        """Validate that items list is not empty."""
        if not self.items:
            raise ValueError("Sale must have at least one item")
        return self


class SaleCancelRequest(BaseModel):
    """Request to cancel a sale."""

    reason: str = Field(
        min_length=1,
        max_length=500,
        description="Reason for cancellation",
    )


# =============================================================================
# SALE RESPONSE SCHEMAS
# =============================================================================


class SaleResponse(BaseModel):
    """Schema for sale in responses."""

    id: UUID = Field(description="Sale unique identifier")
    sale_number: str = Field(description="Auto-generated sale number (YYYY-NNNNNN)")
    sale_date: datetime = Field(description="Date and time of sale")
    items: list[SaleItemResponse] = Field(description="Sale items")
    subtotal: Decimal = Field(description="Subtotal before discounts")
    discount: Decimal = Field(description="Total discount")
    tax: Decimal = Field(description="Tax amount")
    total: Decimal = Field(description="Final total")
    status: SaleStatus = Field(description="Sale status")
    notes: str | None = Field(default=None, description="Sale notes")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID | None = Field(default=None, description="User who created sale")

    model_config = ConfigDict(from_attributes=True)


class SaleListItem(BaseModel):
    """Simplified sale for list responses."""

    id: UUID
    sale_number: str
    sale_date: datetime
    total: Decimal
    status: SaleStatus
    item_count: int = Field(description="Number of items in sale")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# SUMMARY SCHEMAS
# =============================================================================


class DailySummary(BaseModel):
    """Daily sales summary."""

    summary_date: date = Field(description="Summary date")
    total_transactions: int = Field(description="Number of completed sales")
    gross_sales: Decimal = Field(description="Total sales before discounts")
    total_discounts: Decimal = Field(description="Total discounts applied")
    total_tax: Decimal = Field(description="Total tax collected")
    net_sales: Decimal = Field(description="Net sales (after discounts)")

    model_config = ConfigDict(from_attributes=True)


class SalesSummaryPeriod(BaseModel):
    """Sales summary for a period."""

    date_from: date
    date_to: date
    total_transactions: int
    gross_sales: Decimal
    total_discounts: Decimal
    total_tax: Decimal
    net_sales: Decimal
    average_sale: Decimal = Field(description="Average sale amount")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# FILTER SCHEMAS
# =============================================================================


class SaleFilter(BaseModel):
    """Filter parameters for sale listing."""

    status: SaleStatus | None = Field(default=None, description="Filter by status")
    date_from: date | None = Field(default=None, description="Start date")
    date_to: date | None = Field(default=None, description="End date")
    min_total: Decimal | None = Field(default=None, ge=0, description="Minimum total")
    max_total: Decimal | None = Field(default=None, ge=0, description="Maximum total")

    @field_validator("min_total", "max_total", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | str | Decimal | None) -> Decimal | None:
        """Convert to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))
