"""Models for product import from invoice images.

This module provides Pydantic models for AI-extracted data from
handwritten sales invoices, including products and categories.
"""

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MatchConfidence(str, Enum):
    """Confidence level for product matching."""

    HIGH = "high"  # >= 90% similarity
    MEDIUM = "medium"  # >= 70% similarity
    LOW = "low"  # >= 50% similarity
    NONE = "none"  # < 50% - new product


# =============================================================================
# EXTRACTED DATA MODELS
# =============================================================================


class ExtractedProduct(BaseModel):
    """A single product extracted from an invoice image."""

    quantity: int = Field(ge=1, description="Quantity from invoice line")
    description: str = Field(min_length=1, max_length=500, description="Raw description from invoice")
    unit_price: Decimal = Field(ge=0, description="Unit price from invoice")
    total_price: Decimal = Field(ge=0, description="Total price (qty x unit)")
    suggested_category: str | None = Field(
        default=None,
        description="AI-suggested category for this product",
    )


class ExtractedInvoice(BaseModel):
    """Metadata extracted from an invoice image."""

    supplier_name: str | None = Field(
        default=None,
        description="Supplier name if visible on invoice",
    )
    invoice_number: str | None = Field(
        default=None,
        description="Invoice/receipt number if visible",
    )
    invoice_date: str | None = Field(
        default=None,
        description="Invoice date if visible (raw format)",
    )
    image_index: int = Field(description="Index of the image in batch (0-based)")


class ExtractionResult(BaseModel):
    """Complete extraction result for a single image."""

    invoice: ExtractedInvoice
    products: list[ExtractedProduct]
    extraction_confidence: float = Field(
        ge=0,
        le=1,
        description="Overall confidence of extraction (0-1)",
    )
    raw_text: str | None = Field(
        default=None,
        description="Raw extracted text for debugging",
    )


# =============================================================================
# MATCHING MODELS
# =============================================================================


class ProductMatch(BaseModel):
    """A potential match between extracted product and existing catalog."""

    existing_product_id: UUID
    existing_product_name: str
    existing_product_sku: str
    similarity_score: float = Field(ge=0, le=1, description="Fuzzy match score (0-1)")
    confidence: MatchConfidence


class MatchedProduct(BaseModel):
    """Extracted product with matching information."""

    extracted: ExtractedProduct
    matches: list[ProductMatch] = Field(
        default_factory=list,
        description="Potential matches from existing catalog (sorted by score)",
    )
    is_new_product: bool = Field(
        default=True,
        description="True if no high-confidence match found",
    )
    suggested_name: str | None = Field(
        default=None,
        description="AI-suggested standardized name",
    )
    suggested_description: str | None = Field(
        default=None,
        description="AI-suggested product description",
    )


# =============================================================================
# CATEGORY DETECTION MODELS
# =============================================================================


class DetectedCategory(BaseModel):
    """A category detected or suggested from extracted products."""

    name: str = Field(description="Category name")
    exists_in_catalog: bool = Field(description="Whether category already exists")
    existing_category_id: UUID | None = Field(
        default=None,
        description="ID if category exists",
    )
    product_count: int = Field(
        default=1,
        description="Number of extracted products in this category",
    )


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================


class ImageExtractionRequest(BaseModel):
    """Request to extract products from a single image (base64)."""

    image_base64: str = Field(description="Base64-encoded image data")
    image_type: str = Field(
        default="image/jpeg",
        description="MIME type of the image",
    )


class BatchExtractionResponse(BaseModel):
    """Response for batch image extraction."""

    extractions: list[ExtractionResult] = Field(
        description="Extraction results for each image",
    )
    matched_products: list[MatchedProduct] = Field(
        description="All products with matching info",
    )
    detected_categories: list[DetectedCategory] = Field(
        description="Categories detected from products",
    )
    total_products: int = Field(description="Total products extracted")
    total_images_processed: int = Field(description="Number of images processed")
    processing_time_ms: int = Field(description="Total processing time in ms")


class AutocompleteRequest(BaseModel):
    """Request for AI product autocomplete suggestions."""

    partial_text: str = Field(
        min_length=2,
        max_length=100,
        description="Partial product name/description to complete",
    )
    context: str | None = Field(
        default=None,
        max_length=500,
        description="Additional context (e.g., category, invoice text)",
    )


class AutocompleteSuggestion(BaseModel):
    """A single autocomplete suggestion."""

    name: str = Field(description="Suggested product name")
    description: str = Field(description="Suggested product description")
    category: str | None = Field(default=None, description="Suggested category")


class AutocompleteResponse(BaseModel):
    """Response with autocomplete suggestions."""

    suggestions: list[AutocompleteSuggestion] = Field(
        max_length=5,
        description="Up to 5 autocomplete suggestions",
    )

