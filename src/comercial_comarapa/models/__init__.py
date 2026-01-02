"""Pydantic models (schemas) for request/response validation.

This module exports all models used for API request/response validation.
Models are organized by domain:
- common: Pagination, API responses, error handling
- category: Category CRUD schemas
- product: Product CRUD and filter schemas
- inventory: Inventory movement schemas
- sale: Sale and sale item schemas
- validators: Shared validation functions
"""

# Category models
from comercial_comarapa.models.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithProductCount,
)
from comercial_comarapa.models.common import (
    APIResponse,
    DeleteResponse,
    ErrorDetail,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)

# Inventory models
from comercial_comarapa.models.inventory import (
    MovementFilter,
    MovementReason,
    MovementResponse,
    MovementSummary,
    MovementType,
    StockAdjustmentRequest,
    StockEntryRequest,
    StockExitRequest,
)

# Product models
from comercial_comarapa.models.product import (
    LowStockProduct,
    ProductCreate,
    ProductFilter,
    ProductListItem,
    ProductResponse,
    ProductUpdate,
)

# Sale models
from comercial_comarapa.models.sale import (
    DailySummary,
    SaleCancelRequest,
    SaleCreate,
    SaleFilter,
    SaleItemCreate,
    SaleItemResponse,
    SaleListItem,
    SaleResponse,
    SalesSummaryPeriod,
    SaleStatus,
)

# Validators
from comercial_comarapa.models.validators import (
    decimal_validator,
    decimal_validator_required,
    non_negative_int_validator,
    positive_int_validator,
    strip_string_validator,
    uppercase_string_validator,
)

__all__ = [
    "APIResponse",
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "CategoryWithProductCount",
    "DailySummary",
    "DeleteResponse",
    "ErrorDetail",
    "ErrorResponse",
    "LowStockProduct",
    "MessageResponse",
    "MovementFilter",
    "MovementReason",
    "MovementResponse",
    "MovementSummary",
    "MovementType",
    "PaginatedResponse",
    "PaginationMeta",
    "PaginationParams",
    "ProductCreate",
    "ProductFilter",
    "ProductListItem",
    "ProductResponse",
    "ProductUpdate",
    "SaleCancelRequest",
    "SaleCreate",
    "SaleFilter",
    "SaleItemCreate",
    "SaleItemResponse",
    "SaleListItem",
    "SaleResponse",
    "SaleStatus",
    "SalesSummaryPeriod",
    "StockAdjustmentRequest",
    "StockEntryRequest",
    "StockExitRequest",
    "decimal_validator",
    "decimal_validator_required",
    "non_negative_int_validator",
    "positive_int_validator",
    "strip_string_validator",
    "uppercase_string_validator",
]
