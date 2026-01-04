"""Products API router.

This module provides CRUD endpoints for products, plus search and low-stock alerts.

Endpoints:
    GET    /products           - List all products (with filters)
    GET    /products/low-stock - List low stock products
    GET    /products/search    - Search products by name/SKU
    GET    /products/{id}      - Get product by ID
    GET    /products/sku/{sku} - Get product by SKU
    POST   /products           - Create new product
    PUT    /products/{id}      - Update product
    DELETE /products/{id}      - Soft delete product
"""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from comercial_comarapa.api.v1.deps import get_product_service
from comercial_comarapa.models.common import (
    APIResponse,
    DeleteResponse,
    PaginatedResponse,
    PaginationParams,
)
from comercial_comarapa.models.product import (
    LowStockProduct,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from comercial_comarapa.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="List all products",
    description="Get a paginated list of products with optional filters.",
)
def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    category_id: Annotated[UUID | None, Query(description="Filter by category")] = None,
    min_price: Annotated[Decimal | None, Query(ge=0, description="Minimum price")] = None,
    max_price: Annotated[Decimal | None, Query(ge=0, description="Maximum price")] = None,
    in_stock: Annotated[bool | None, Query(description="Filter by stock availability")] = None,
    is_active: Annotated[bool, Query(description="Filter by active status")] = True,
) -> PaginatedResponse[ProductResponse]:
    """List all products with pagination and filters."""
    pagination = PaginationParams(page=page, page_size=page_size)
    products, meta = service.list_products(
        pagination=pagination,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        is_active=is_active,
    )
    return PaginatedResponse(data=products, pagination=meta)


@router.get(
    "/low-stock",
    response_model=APIResponse[list[LowStockProduct]],
    summary="Get low stock products",
    description="Get products with stock below minimum level.",
)
def get_low_stock_products(
    service: Annotated[ProductService, Depends(get_product_service)],
) -> APIResponse[list[LowStockProduct]]:
    """Get products with low stock."""
    products = service.get_low_stock_products()
    return APIResponse(data=products)


@router.get(
    "/search",
    response_model=APIResponse[list[ProductResponse]],
    summary="Search products",
    description="Search products by name or SKU (case-insensitive).",
)
def search_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    q: Annotated[str, Query(min_length=1, max_length=100, description="Search term")],
    limit: Annotated[int, Query(ge=1, le=50, description="Max results")] = 20,
) -> APIResponse[list[ProductResponse]]:
    """Search products by name or SKU."""
    products = service.search_products(term=q, limit=limit)
    return APIResponse(data=products)


@router.get(
    "/sku/{sku}",
    response_model=APIResponse[ProductResponse],
    summary="Get product by SKU",
    description="Get a single product by its SKU.",
    responses={
        404: {"description": "Product not found"},
    },
)
def get_product_by_sku(
    sku: str,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> APIResponse[ProductResponse]:
    """Get a product by SKU."""
    product = service.get_product_by_sku(sku)
    return APIResponse(data=product)


@router.get(
    "/{product_id}",
    response_model=APIResponse[ProductResponse],
    summary="Get product by ID",
    description="Get a single product by its unique identifier.",
    responses={
        404: {"description": "Product not found"},
    },
)
def get_product(
    product_id: UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> APIResponse[ProductResponse]:
    """Get a product by ID."""
    product = service.get_product(product_id)
    return APIResponse(data=product)


@router.post(
    "",
    response_model=APIResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new product",
    description="Create a new product. SKU must be unique.",
    responses={
        409: {"description": "Product SKU already exists"},
    },
)
def create_product(
    data: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> APIResponse[ProductResponse]:
    """Create a new product."""
    product = service.create_product(data)
    return APIResponse(data=product, message="Product created successfully")


@router.put(
    "/{product_id}",
    response_model=APIResponse[ProductResponse],
    summary="Update product",
    description="Update an existing product. All fields are optional.",
    responses={
        404: {"description": "Product not found"},
        409: {"description": "Product SKU already exists"},
    },
)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> APIResponse[ProductResponse]:
    """Update an existing product."""
    product = service.update_product(product_id, data)
    return APIResponse(data=product, message="Product updated successfully")


@router.delete(
    "/{product_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete product",
    description="Soft delete a product (sets is_active=False).",
    responses={
        404: {"description": "Product not found"},
    },
)
def delete_product(
    product_id: UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> DeleteResponse:
    """Soft delete a product."""
    service.delete_product(product_id)
    return DeleteResponse(id=product_id, message="Product deleted successfully")
