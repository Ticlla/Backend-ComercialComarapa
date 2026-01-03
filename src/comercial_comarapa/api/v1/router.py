"""API v1 router aggregation.

This module creates the main v1 router that includes all
sub-routers for different resources.

Usage:
    from comercial_comarapa.api.v1.router import api_router

    app.include_router(api_router, prefix="/api/v1")
"""

from fastapi import APIRouter

from comercial_comarapa.api.v1.categories import router as categories_router
from comercial_comarapa.api.v1.inventory import router as inventory_router
from comercial_comarapa.api.v1.products import router as products_router

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
