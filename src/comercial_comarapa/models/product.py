"""Product models for request/response validation."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from comercial_comarapa.models.category import CategoryResponse

# =============================================================================
# BASE SCHEMA
# =============================================================================


class ProductBase(BaseModel):
    """Base product schema with common fields."""

    sku: str = Field(
        min_length=1,
        max_length=50,
        description="Stock Keeping Unit (unique identifier)",
        examples=["BEB-001"],
    )
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Product name",
        examples=["Coca Cola 2L"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Product description",
        examples=["Gaseosa Coca Cola botella 2 litros"],
    )
    category_id: UUID | None = Field(
        default=None,
        description="Category ID (optional)",
    )
    unit_price: Decimal = Field(
        ge=0,
        decimal_places=2,
        description="Selling price per unit",
        examples=[15.00],
    )
    cost_price: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Cost price per unit (optional)",
        examples=[12.00],
    )
    min_stock_level: int = Field(
        default=5,
        ge=0,
        description="Minimum stock level for alerts",
        examples=[10],
    )

    @field_validator("unit_price", "cost_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | str | Decimal | None) -> Decimal | None:
        """Convert price values to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields optional for partial updates."""

    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    category_id: UUID | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    cost_price: Decimal | None = Field(default=None, ge=0)
    min_stock_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    @field_validator("unit_price", "cost_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | str | Decimal | None) -> Decimal | None:
        """Convert price values to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class ProductResponse(ProductBase):
    """Schema for product in responses."""

    id: UUID = Field(description="Product unique identifier")
    current_stock: int = Field(description="Current stock quantity")
    is_active: bool = Field(description="Whether product is active")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    category: CategoryResponse | None = Field(
        default=None,
        description="Category details (if included)",
    )

    model_config = ConfigDict(from_attributes=True)


class ProductListItem(BaseModel):
    """Simplified product for list responses."""

    id: UUID
    sku: str
    name: str
    category_id: UUID | None
    category_name: str | None = None
    unit_price: Decimal
    current_stock: int
    min_stock_level: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_low_stock(self) -> bool:
        """Check if product is below minimum stock level."""
        return self.current_stock <= self.min_stock_level


class LowStockProduct(BaseModel):
    """Product with low stock alert info."""

    id: UUID
    sku: str
    name: str
    category_name: str | None
    current_stock: int
    min_stock_level: int
    units_needed: int = Field(description="Units needed to reach min level")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# FILTER SCHEMAS
# =============================================================================


class ProductFilter(BaseModel):
    """Filter parameters for product listing."""

    category_id: UUID | None = Field(default=None, description="Filter by category")
    min_price: Decimal | None = Field(default=None, ge=0, description="Minimum price")
    max_price: Decimal | None = Field(default=None, ge=0, description="Maximum price")
    in_stock: bool | None = Field(default=None, description="Filter by stock availability")
    is_active: bool = Field(default=True, description="Filter by active status")
    search: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Search in name and SKU",
    )

    @field_validator("min_price", "max_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v: float | str | Decimal | None) -> Decimal | None:
        """Convert price values to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))
