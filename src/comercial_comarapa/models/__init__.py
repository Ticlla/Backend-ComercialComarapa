"""Pydantic models (schemas) for request/response validation.

This module exports all models used for API request/response validation.
Models are organized by domain:
- common: Pagination, API responses, error handling
- category: Category CRUD schemas
- product: Product CRUD and filter schemas
- inventory: Inventory movement schemas
- sale: Sale and sale item schemas
"""

# Common models
# Category models
from comercial_comarapa.models.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithProductCount,
)
from comercial_comarapa.models.common import (
    APIResponse,
    AuditMixin,
    DeleteResponse,
    ErrorDetail,
    ErrorResponse,
    IDMixin,
    MessageResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    TimestampMixin,
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

__all__ = [
    "APIResponse",
    "AuditMixin",
    "CategoryCreate",
    "CategoryResponse",
    "CategoryUpdate",
    "CategoryWithProductCount",
    "DailySummary",
    "DeleteResponse",
    "ErrorDetail",
    "ErrorResponse",
    "IDMixin",
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
    "TimestampMixin",
]
