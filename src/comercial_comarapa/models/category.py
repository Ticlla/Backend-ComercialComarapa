"""Category models for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# BASE SCHEMA
# =============================================================================


class CategoryBase(BaseModel):
    """Base category schema with common fields."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Category name (unique)",
        examples=["Bebidas"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Category description",
        examples=["Refrescos, jugos, agua y bebidas en general"],
    )


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category. All fields optional for partial updates."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Category name (unique)",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Category description",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class CategoryResponse(CategoryBase):
    """Schema for category in responses."""

    id: UUID = Field(description="Category unique identifier")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class CategoryWithProductCount(CategoryResponse):
    """Category response with product count."""

    product_count: int = Field(default=0, description="Number of products in this category")
