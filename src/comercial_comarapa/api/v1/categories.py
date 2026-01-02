"""Categories API router.

This module provides CRUD endpoints for product categories.

Endpoints:
    GET    /categories          - List all categories
    GET    /categories/{id}     - Get category by ID
    POST   /categories          - Create new category
    PUT    /categories/{id}     - Update category
    DELETE /categories/{id}     - Delete category
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from comercial_comarapa.api.v1.deps import get_category_service
from comercial_comarapa.models.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from comercial_comarapa.models.common import (
    APIResponse,
    DeleteResponse,
    PaginatedResponse,
    PaginationParams,
)
from comercial_comarapa.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=PaginatedResponse[CategoryResponse],
    summary="List all categories",
    description="Get a paginated list of all product categories.",
)
async def list_categories(
    service: Annotated[CategoryService, Depends(get_category_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> PaginatedResponse[CategoryResponse]:
    """List all categories with pagination."""
    pagination = PaginationParams(page=page, page_size=page_size)
    categories, meta = service.list_categories(pagination)
    return PaginatedResponse(data=categories, pagination=meta)


@router.get(
    "/{category_id}",
    response_model=APIResponse[CategoryResponse],
    summary="Get category by ID",
    description="Get a single category by its unique identifier.",
    responses={
        404: {"description": "Category not found"},
    },
)
async def get_category(
    category_id: UUID,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> APIResponse[CategoryResponse]:
    """Get a category by ID."""
    category = service.get_category(category_id)
    return APIResponse(data=category)


@router.post(
    "",
    response_model=APIResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new category",
    description="Create a new product category. Name must be unique.",
    responses={
        409: {"description": "Category name already exists"},
    },
)
async def create_category(
    data: CategoryCreate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> APIResponse[CategoryResponse]:
    """Create a new category."""
    category = service.create_category(data)
    return APIResponse(data=category, message="Category created successfully")


@router.put(
    "/{category_id}",
    response_model=APIResponse[CategoryResponse],
    summary="Update category",
    description="Update an existing category. All fields are optional.",
    responses={
        404: {"description": "Category not found"},
        409: {"description": "Category name already exists"},
    },
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> APIResponse[CategoryResponse]:
    """Update an existing category."""
    category = service.update_category(category_id, data)
    return APIResponse(data=category, message="Category updated successfully")


@router.delete(
    "/{category_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete category",
    description="Delete a category. Cannot delete if category has associated products.",
    responses={
        404: {"description": "Category not found"},
        400: {"description": "Category has associated products"},
    },
)
async def delete_category(
    category_id: UUID,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> DeleteResponse:
    """Delete a category."""
    service.delete_category(category_id)
    return DeleteResponse(id=category_id, message="Category deleted successfully")
