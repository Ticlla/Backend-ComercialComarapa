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
    BulkCreateRequest,
    BulkCreateResponse,
    BulkCreateResultItem,
    ExtractionResult,
    ImageExtractionRequest,
    MatchProductRequest,
    MatchProductResponse,
)
from comercial_comarapa.models.product import ProductCreate
from comercial_comarapa.services.ai_extraction_service import AIExtractionService
from comercial_comarapa.services.matching_service import MatchingService

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
    description="Extract product information from a single invoice image using AI Vision. "
    "Categories from the database are automatically used for better suggestions.",
)
async def extract_from_image(
    request: ImageExtractionRequest,
    ai_service: Annotated[AIExtractionService, Depends(get_ai_service)],
    db: Annotated[DatabaseClientProtocol, Depends(get_db)],
) -> ExtractionResult:
    """Extract products from a single base64-encoded image.

    Args:
        request: Image extraction request with base64 data.
        ai_service: AI extraction service.
        db: Database client for fetching categories.

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

    # Fetch categories from database for better AI suggestions
    category_repo = CategoryRepository(db)
    categories_response, _ = category_repo.list()
    categories = [
        {"name": c.name, "description": c.description}
        for c in categories_response
    ]

    try:
        result = await ai_service.extract_from_image(
            image_base64=request.image_base64,
            image_type=request.image_type,
            categories=categories,
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

    # Fetch categories for AI prompt (before extraction)
    category_repo = CategoryRepository(db)
    existing_categories_response, _ = category_repo.list()
    categories_for_prompt = [
        {"name": c.name, "description": c.description}
        for c in existing_categories_response
    ]

    try:
        # Extract from all images with dynamic categories
        extractions, _extraction_time_ms = await ai_service.extract_from_images_batch(
            images,
            categories=categories_for_prompt,
        )

        # Use MatchingService for database-powered fuzzy matching (pg_trgm)
        matching_service = MatchingService(db)

        # Get existing categories for matching
        existing_categories_dict = [
            {"id": c.id, "name": c.name}
            for c in existing_categories_response
        ]

        # Match extracted products with catalog using database fuzzy search
        matched_products, detected_categories = matching_service.match_extraction_results(
            extractions=extractions,
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
    description="Get AI-powered autocomplete suggestions for product name and description. "
    "Uses categories from the database for relevant suggestions.",
)
async def autocomplete_product(
    request: AutocompleteRequest,
    ai_service: Annotated[AIExtractionService, Depends(get_ai_service)],
    db: Annotated[DatabaseClientProtocol, Depends(get_db)],
) -> AutocompleteResponse:
    """Get AI autocomplete suggestions for product.

    Args:
        request: Autocomplete request with partial text.
        ai_service: AI extraction service.
        db: Database client for fetching categories.

    Returns:
        AutocompleteResponse with suggestions.

    Raises:
        HTTPException: If autocomplete fails.
    """
    logger.info("autocomplete_request", partial_text=request.partial_text)

    # Fetch categories for better suggestions
    category_repo = CategoryRepository(db)
    categories_response, _ = category_repo.list()
    categories = [{"name": c.name} for c in categories_response]

    try:
        return await ai_service.get_autocomplete_suggestions(
            partial_text=request.partial_text,
            context=request.context,
            categories=categories,
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


@router.post(
    "/match-products",
    response_model=MatchProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Match product description against catalog",
    description="Use database fuzzy search (pg_trgm) to find matching products in the catalog.",
)
async def match_products(
    request: MatchProductRequest,
    db: Annotated[DatabaseClientProtocol, Depends(get_db)],
) -> MatchProductResponse:
    """Match a product description against existing catalog.

    Uses PostgreSQL's pg_trgm extension for accurate fuzzy matching.

    Args:
        request: Match request with product description.
        db: Database client.

    Returns:
        MatchProductResponse with matches and suggestions.
    """
    logger.info("match_products_request", description=request.description[:30])

    start_time = time.time()

    # Use MatchingService for database fuzzy search
    matching_service = MatchingService(db)
    matched = matching_service.match_single_product(
        description=request.description,
        suggested_category=request.suggested_category,
    )

    processing_time_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "match_products_complete",
        matches_count=len(matched.matches),
        is_new=matched.is_new_product,
        time_ms=processing_time_ms,
    )

    return MatchProductResponse(
        matched=matched,
        processing_time_ms=processing_time_ms,
    )


def _generate_sku(category_prefix: str) -> str:
    """Generate a unique SKU for a new product.

    Args:
        category_prefix: Category prefix (e.g., 'LIM' for Limpieza).

    Returns:
        Generated SKU (e.g., 'LIM-A1B2C3').
    """
    import uuid  # noqa: PLC0415

    # Use UUID suffix for uniqueness
    unique_suffix = str(uuid.uuid4())[:6].upper()
    return f"{category_prefix}-{unique_suffix}"


@router.post(
    "/bulk-create",
    response_model=BulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple products at once",
    description="Bulk create products from extracted/corrected invoice data.",
)
async def bulk_create_products(
    request: BulkCreateRequest,
    db: Annotated[DatabaseClientProtocol, Depends(get_db)],
) -> BulkCreateResponse:
    """Create multiple products at once.

    Handles:
    - Auto-creation of missing categories (if enabled)
    - SKU generation
    - Individual error handling (one failure doesn't stop others)

    Args:
        request: Bulk creation request with products.
        db: Database client.

    Returns:
        BulkCreateResponse with individual results.
    """
    logger.info("bulk_create_request", product_count=len(request.products))

    start_time = time.time()
    results: list[BulkCreateResultItem] = []
    categories_created = 0

    # Repositories
    product_repo = ProductRepository(db)
    category_repo = CategoryRepository(db)

    # Cache for categories (name -> id)
    category_cache: dict[str, str] = {}

    # Fetch existing categories
    existing_categories, _ = category_repo.list()
    for cat in existing_categories:
        category_cache[cat.name.lower()] = str(cat.id)

    for idx, item in enumerate(request.products):
        try:
            # Resolve category
            category_id = item.category_id

            if not category_id and item.category_name:
                cat_lower = item.category_name.lower()

                if cat_lower in category_cache:
                    category_id = category_cache[cat_lower]  # type: ignore
                elif request.create_missing_categories:
                    # Create new category
                    from comercial_comarapa.models.category import (  # noqa: PLC0415
                        CategoryCreate,
                    )

                    new_cat = category_repo.create(
                        CategoryCreate(
                            name=item.category_name,
                            description=f"Auto-created from import: {item.category_name}",
                        )
                    )
                    category_cache[cat_lower] = str(new_cat.id)
                    category_id = new_cat.id  # type: ignore
                    categories_created += 1
                    logger.info("category_auto_created", name=item.category_name)

            # Generate SKU
            category_prefix = item.category_name[:3].upper() if item.category_name else "GEN"
            sku = _generate_sku(category_prefix)

            # Create product
            product = product_repo.create(
                ProductCreate(
                    sku=sku,
                    name=item.name,
                    description=item.description,
                    category_id=category_id,  # type: ignore
                    unit_price=item.unit_price,
                    cost_price=item.cost_price,
                    min_stock_level=item.min_stock_level,
                )
            )

            results.append(
                BulkCreateResultItem(
                    index=idx,
                    success=True,
                    product_id=product.id,
                    product_sku=product.sku,
                )
            )

            logger.debug("product_created", index=idx, sku=sku, name=item.name[:30])

        except Exception as e:
            logger.error("product_creation_failed", index=idx, error=str(e))
            # Sanitize error message - don't expose internal details
            error_msg = "Failed to create product. Please check your data."
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                error_msg = "Product with this name or SKU already exists."
            elif "foreign key" in str(e).lower():
                error_msg = "Invalid category reference."
            elif "validation" in str(e).lower():
                error_msg = "Invalid product data. Please check required fields."
            results.append(
                BulkCreateResultItem(
                    index=idx,
                    success=False,
                    error=error_msg,
                )
            )

    total_created = sum(1 for r in results if r.success)
    total_failed = sum(1 for r in results if not r.success)
    processing_time_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "bulk_create_complete",
        total=len(request.products),
        created=total_created,
        failed=total_failed,
        categories_created=categories_created,
        time_ms=processing_time_ms,
    )

    return BulkCreateResponse(
        total_requested=len(request.products),
        total_created=total_created,
        total_failed=total_failed,
        results=results,
        categories_created=categories_created,
        processing_time_ms=processing_time_ms,
    )


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

