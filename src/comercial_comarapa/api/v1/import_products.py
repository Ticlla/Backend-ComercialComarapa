"""Product Import API endpoints.

This module provides endpoints for importing products from
invoice images using AI Vision extraction.

Usage:
    from comercial_comarapa.api.v1.import_products import router
"""

from __future__ import annotations

import base64
import time
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from comercial_comarapa.api.v1.deps import get_db
from comercial_comarapa.core.exceptions import AIExtractionError
from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.core.protocols import DatabaseClientProtocol
from comercial_comarapa.db.repositories.category import CategoryRepository
from comercial_comarapa.db.repositories.product import ProductRepository
from comercial_comarapa.models.import_extraction import (
    AutocompleteRequest,
    AutocompleteResponse,
    BatchExtractionResponse,
    ExtractionResult,
    ImageExtractionRequest,
)
from comercial_comarapa.services.ai_extraction_service import AIExtractionService

logger = get_logger(__name__)

router = APIRouter(prefix="/import", tags=["Product Import"])

# =============================================================================
# CONSTANTS
# =============================================================================

MAX_IMAGE_SIZE_MB = 10
MAX_IMAGES_PER_BATCH = 20
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_ai_service() -> AIExtractionService:
    """Get AI extraction service instance."""
    return AIExtractionService()


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/extract-from-image",
    response_model=ExtractionResult,
    status_code=status.HTTP_200_OK,
    summary="Extract products from single image",
    description="Extract product information from a single invoice image using AI Vision.",
)
async def extract_from_image(
    request: ImageExtractionRequest,
    ai_service: Annotated[AIExtractionService, Depends(get_ai_service)],
) -> ExtractionResult:
    """Extract products from a single base64-encoded image.

    Args:
        request: Image extraction request with base64 data.
        ai_service: AI extraction service.

    Returns:
        ExtractionResult with extracted products.

    Raises:
        HTTPException: If extraction fails.
    """
    logger.info("extract_from_image_request")

    # Validate image type
    if request.image_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    # Validate image size (rough estimate from base64)
    estimated_size_mb = len(request.image_base64) * 3 / 4 / 1024 / 1024
    if estimated_size_mb > MAX_IMAGE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE_MB}MB",
        )

    try:
        result = await ai_service.extract_from_image(
            image_base64=request.image_base64,
            image_type=request.image_type,
        )
        return result
    except AIExtractionError as e:
        logger.error("extraction_failed", error=str(e))
        # Sanitize error message - don't expose internal details
        user_message = "Failed to extract products from image. Please try again."
        if "not configured" in str(e).lower():
            user_message = "AI service is not configured. Please contact support."
        elif "quota" in str(e).lower() or "rate" in str(e).lower():
            user_message = "AI service temporarily unavailable. Please try again later."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message,
        ) from e


@router.post(
    "/extract-from-images",
    response_model=BatchExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract products from multiple images",
    description="Extract product information from multiple invoice images (up to 20) using AI Vision.",
)
async def extract_from_images(
    files: Annotated[list[UploadFile], File(description="Invoice images (max 20)")],
    ai_service: Annotated[AIExtractionService, Depends(get_ai_service)],
    db: Annotated[DatabaseClientProtocol, Depends(get_db)],
) -> BatchExtractionResponse:
    """Extract products from multiple uploaded images.

    Args:
        files: List of uploaded image files.
        ai_service: AI extraction service.
        db: Database client for matching.

    Returns:
        BatchExtractionResponse with all extracted and matched products.

    Raises:
        HTTPException: If validation or extraction fails.
    """
    logger.info("extract_from_images_request", files_count=len(files))

    # Validate number of files
    if len(files) > MAX_IMAGES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many images. Maximum: {MAX_IMAGES_PER_BATCH}",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No images provided",
        )

    # Validate and prepare images
    images: list[tuple[str, str]] = []

    for idx, file in enumerate(files):
        # Validate content type
        content_type = file.content_type or "image/jpeg"
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image {idx + 1}: Unsupported type '{content_type}'",
            )

        # Read and encode
        content = await file.read()

        # Validate size
        size_mb = len(content) / 1024 / 1024
        if size_mb > MAX_IMAGE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image {idx + 1}: Too large ({size_mb:.1f}MB). Max: {MAX_IMAGE_SIZE_MB}MB",
            )

        # Encode to base64
        image_base64 = base64.b64encode(content).decode("utf-8")
        images.append((image_base64, content_type))

    start_time = time.time()

    try:
        # Extract from all images
        extractions, _extraction_time_ms = await ai_service.extract_from_images_batch(images)

        # Get existing products and categories for matching
        product_repo = ProductRepository(db)
        category_repo = CategoryRepository(db)

        # Fetch existing items for matching
        existing_products_response, _ = product_repo.list_with_filters(is_active=True)
        existing_products = [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
            }
            for p in existing_products_response
        ]

        existing_categories_response, _ = category_repo.list()
        existing_categories_dict = [
            {
                "id": c.id,
                "name": c.name,
            }
            for c in existing_categories_response
        ]

        # Match extracted products with catalog
        matched_products, detected_categories = ai_service.match_with_catalog(
            extractions=extractions,
            existing_products=existing_products,
            existing_categories=existing_categories_dict,
        )

        total_time_ms = int((time.time() - start_time) * 1000)

        return BatchExtractionResponse(
            extractions=extractions,
            matched_products=matched_products,
            detected_categories=detected_categories,
            total_products=sum(len(e.products) for e in extractions),
            total_images_processed=len(files),
            processing_time_ms=total_time_ms,
        )

    except AIExtractionError as e:
        logger.error("batch_extraction_failed", error=str(e))
        # Sanitize error message - don't expose internal details
        user_message = "Failed to extract products from images. Please try again."
        if "not configured" in str(e).lower():
            user_message = "AI service is not configured. Please contact support."
        elif "quota" in str(e).lower() or "rate" in str(e).lower():
            user_message = "AI service temporarily unavailable. Please try again later."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message,
        ) from e


@router.post(
    "/autocomplete-product",
    response_model=AutocompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI autocomplete suggestions",
    description="Get AI-powered autocomplete suggestions for product name and description.",
)
async def autocomplete_product(
    request: AutocompleteRequest,
    ai_service: Annotated[AIExtractionService, Depends(get_ai_service)],
) -> AutocompleteResponse:
    """Get AI autocomplete suggestions for product.

    Args:
        request: Autocomplete request with partial text.
        ai_service: AI extraction service.

    Returns:
        AutocompleteResponse with suggestions.

    Raises:
        HTTPException: If autocomplete fails.
    """
    logger.info("autocomplete_request", partial_text=request.partial_text)

    try:
        return await ai_service.get_autocomplete_suggestions(
            partial_text=request.partial_text,
            context=request.context,
        )
    except AIExtractionError as e:
        logger.error("autocomplete_failed", error=str(e))
        # Sanitize error message - don't expose internal details
        user_message = "Failed to get suggestions. Please try again."
        if "not configured" in str(e).lower():
            user_message = "AI service is not configured. Please contact support."
        elif "quota" in str(e).lower() or "rate" in str(e).lower():
            user_message = "AI service temporarily unavailable. Please try again later."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message,
        ) from e


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check import service health",
    description="Check if AI extraction service is properly configured.",
)
async def import_health_check() -> dict:
    """Check if import service is healthy.

    Returns:
        Health status with configuration info.
    """
    from comercial_comarapa.config import settings  # noqa: PLC0415

    is_configured = bool(settings.gemini_api_key)

    return {
        "status": "healthy" if is_configured else "degraded",
        "ai_configured": is_configured,
        "ai_model": settings.gemini_model if is_configured else None,
        "max_images_per_batch": MAX_IMAGES_PER_BATCH,
        "max_image_size_mb": MAX_IMAGE_SIZE_MB,
    }

