"""Inventory API router.

This module provides endpoints for inventory management:
stock entries, exits, adjustments, and movement history.

Endpoints:
    GET    /inventory/movements              - List all movements
    GET    /inventory/movements/{product_id} - Get movements by product
    POST   /inventory/entry                  - Register stock entry
    POST   /inventory/exit                   - Register stock exit
    POST   /inventory/adjustment             - Adjust stock level
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from comercial_comarapa.api.v1.deps import get_inventory_service
from comercial_comarapa.models.common import (
    APIResponse,
    PaginatedResponse,
    PaginationParams,
)
from comercial_comarapa.models.inventory import (
    MovementReason,
    MovementResponse,
    MovementType,
    StockAdjustmentRequest,
    StockEntryRequest,
    StockExitRequest,
)
from comercial_comarapa.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get(
    "/movements",
    response_model=PaginatedResponse[MovementResponse],
    summary="List all movements",
    description="Get a paginated list of all inventory movements with optional filters.",
)
def list_movements(
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    product_id: Annotated[UUID | None, Query(description="Filter by product")] = None,
    movement_type: Annotated[
        MovementType | None, Query(description="Filter by movement type")
    ] = None,
    reason: Annotated[MovementReason | None, Query(description="Filter by reason")] = None,
    date_from: Annotated[datetime | None, Query(description="Start date")] = None,
    date_to: Annotated[datetime | None, Query(description="End date")] = None,
) -> PaginatedResponse[MovementResponse]:
    """List all inventory movements with pagination and filters."""
    pagination = PaginationParams(page=page, page_size=page_size)
    movements, meta = service.list_movements(
        pagination=pagination,
        product_id=product_id,
        movement_type=movement_type,
        reason=reason,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedResponse(data=movements, pagination=meta)


@router.get(
    "/movements/{product_id}",
    response_model=APIResponse[list[MovementResponse]],
    summary="Get movements by product",
    description="Get movement history for a specific product.",
    responses={
        404: {"description": "Product not found"},
    },
)
def get_movements_by_product(
    product_id: UUID,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="Max movements")] = 50,
) -> APIResponse[list[MovementResponse]]:
    """Get movement history for a product."""
    movements = service.get_movements_by_product(product_id, limit=limit)
    return APIResponse(data=movements)


@router.post(
    "/entry",
    response_model=APIResponse[MovementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register stock entry",
    description="Add stock to a product. Creates an ENTRY movement record.",
    responses={
        404: {"description": "Product not found"},
    },
)
def stock_entry(
    data: StockEntryRequest,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> APIResponse[MovementResponse]:
    """Register a stock entry (add stock)."""
    movement = service.stock_entry(data)
    return APIResponse(
        data=movement,
        message=f"Stock entry successful. New stock: {movement.new_stock}",
    )


@router.post(
    "/exit",
    response_model=APIResponse[MovementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register stock exit",
    description="Remove stock from a product. Creates an EXIT movement record.",
    responses={
        400: {"description": "Insufficient stock"},
        404: {"description": "Product not found"},
    },
)
def stock_exit(
    data: StockExitRequest,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> APIResponse[MovementResponse]:
    """Register a stock exit (remove stock)."""
    movement = service.stock_exit(data)
    return APIResponse(
        data=movement,
        message=f"Stock exit successful. New stock: {movement.new_stock}",
    )


@router.post(
    "/adjustment",
    response_model=APIResponse[MovementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Adjust stock level",
    description="Set stock to a specific value. Creates an ADJUSTMENT movement record.",
    responses={
        404: {"description": "Product not found"},
    },
)
def stock_adjustment(
    data: StockAdjustmentRequest,
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> APIResponse[MovementResponse]:
    """Adjust stock to a specific value."""
    movement = service.stock_adjustment(data)
    return APIResponse(
        data=movement,
        message=f"Stock adjustment successful. New stock: {movement.new_stock}",
    )

