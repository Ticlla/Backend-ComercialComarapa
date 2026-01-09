"""AI Extraction Service for invoice images.

This module provides the AIExtractionService class that uses
Google Gemini Flash Vision to extract product information from
handwritten sales invoices.

Uses Jinja2 templates for dynamic prompt generation with
categories from the database.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import google.generativeai as genai

# TODO: Migrate to google.genai package when ready
# The deprecated google.generativeai package doesn't properly support
# response_schema with TypedDict. When migrating to google.genai:
# 1. Use response_schema for structured output enforcement
# 2. Remove defensive JSON extraction (extract_json_from_response)
# 3. Remove list response unwrapping logic
# See: https://github.com/google-gemini/deprecated-generative-ai-python
from comercial_comarapa.config import settings
from comercial_comarapa.core.exceptions import AIExtractionError
from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.models.import_extraction import (
    AutocompleteResponse,
    AutocompleteSuggestion,
    DetectedCategory,
    ExtractedInvoice,
    ExtractedProduct,
    ExtractionResult,
    MatchConfidence,
    MatchedProduct,
    ProductMatch,
)
from comercial_comarapa.prompts.template_service import get_template_service

logger = get_logger(__name__)


def _find_json_end(text: str) -> int | None:
    """Find the index of the closing brace of a JSON object.

    Args:
        text: Text starting with '{'.

    Returns:
        Index of closing '}' or None if not found.
    """
    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return i
    return None


def extract_json_from_response(text: str) -> dict[str, Any]:
    """Extract valid JSON object from potentially malformed response.

    Gemini sometimes appends garbage text after valid JSON.
    This function finds and extracts the valid JSON portion.

    Args:
        text: Raw response text that may contain valid JSON followed by garbage.

    Returns:
        Parsed JSON dictionary.

    Raises:
        json.JSONDecodeError: If no valid JSON can be extracted.
    """
    text = text.strip()

    # First, try parsing as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the end of the JSON object by counting braces
    if text.startswith("{"):
        end_idx = _find_json_end(text)
        if end_idx is not None:
            try:
                return json.loads(text[: end_idx + 1])
            except json.JSONDecodeError:
                pass

    # Last resort: raise the original error
    raise json.JSONDecodeError("Could not extract valid JSON from response", text, 0)


class AIExtractionService:
    """Service for AI-powered product extraction from invoice images.

    Uses Google Gemini Flash Vision to process handwritten invoices
    and extract structured product information.

    Now supports dynamic category injection via Jinja2 templates.

    Example:
        service = AIExtractionService()

        # With dynamic categories from database
        categories = [{"name": "Limpieza", "description": "Productos de limpieza"}]
        result = await service.extract_from_image(
            image_base64="...",
            categories=categories
        )
    """

    def __init__(self) -> None:
        """Initialize the AI extraction service."""
        self._template_service = get_template_service()

        if not settings.gemini_api_key:
            logger.warning("gemini_api_key_not_configured")
        else:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
            logger.info("ai_extraction_service_initialized", model=settings.gemini_model)

    def _is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(settings.gemini_api_key)

    async def extract_from_image(
        self,
        image_base64: str,
        image_type: str = "image/jpeg",
        image_index: int = 0,
        categories: list[dict[str, Any]] | None = None,
    ) -> ExtractionResult:
        """Extract products from a single invoice image.

        Args:
            image_base64: Base64-encoded image data.
            image_type: MIME type of the image.
            image_index: Index of image in batch.
            categories: Optional list of categories from database.
                       Each dict should have 'name' and optionally 'description'.

        Returns:
            ExtractionResult with extracted products and metadata.

        Raises:
            AIExtractionError: If extraction fails.
        """
        if not self._is_configured():
            raise AIExtractionError("Gemini API key not configured")

        logger.info(
            "extracting_from_image",
            image_index=image_index,
            categories_count=len(categories) if categories else 0,
        )

        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Render prompt with categories (uses Jinja2 template)
            extraction_prompt = self._template_service.render_extraction_prompt(
                categories=categories,
                default_category="Otros",
            )

            # Create content for Gemini
            # Note: response_schema with TypedDict doesn't work well with deprecated
            # google.generativeai package - it causes empty products. Using only
            # response_mime_type with defensive JSON parsing instead.
            response = self.model.generate_content(
                [
                    extraction_prompt,
                    {"mime_type": image_type, "data": image_data},
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature for accuracy
                    max_output_tokens=8192,  # Ensure response isn't truncated
                ),
            )

            # Parse response
            result_text = response.text.strip()

            # Log raw response length for debugging truncation issues
            logger.debug(
                "gemini_raw_response",
                image_index=image_index,
                response_length=len(result_text),
                response_preview=result_text[:200] if len(result_text) > 200 else result_text,
            )

            try:
                # Use defensive JSON extraction to handle malformed responses
                result_data = extract_json_from_response(result_text)
            except json.JSONDecodeError as parse_error:
                # Log the problematic response for debugging
                logger.error(
                    "json_parse_failed",
                    image_index=image_index,
                    error=str(parse_error),
                    response_length=len(result_text),
                    response_tail=result_text[-100:] if len(result_text) > 100 else result_text,
                )
                raise

            # Log raw response for debugging (only structure, not full data)
            logger.debug(
                "gemini_response_structure",
                image_index=image_index,
                response_type=type(result_data).__name__,
                has_invoice="invoice" in result_data if isinstance(result_data, dict) else False,
                has_products="products" in result_data if isinstance(result_data, dict) else False,
            )

            # Handle list response - Gemini sometimes wraps the result in a list
            if isinstance(result_data, list):
                logger.warning(
                    "unexpected_list_response",
                    image_index=image_index,
                    list_length=len(result_data),
                )
                if len(result_data) == 1 and isinstance(result_data[0], dict):
                    # Check if it's a wrapped extraction result
                    first_item = result_data[0]
                    if "products" in first_item or "invoice" in first_item:
                        # Gemini wrapped the proper response in a list - unwrap it
                        logger.info("unwrapping_list_response", image_index=image_index)
                        result_data = first_item
                    else:
                        # Single product in a list
                        result_data = {"products": result_data, "extraction_confidence": 0.5}
                else:
                    # Assume it's a list of products directly
                    result_data = {"products": result_data, "extraction_confidence": 0.5}

            # Ensure result_data is a dict
            if not isinstance(result_data, dict):
                logger.error("unexpected_response_type", response_type=type(result_data).__name__)
                raise AIExtractionError(f"Unexpected response type: {type(result_data).__name__}")

            # Check for error response (now within the structured object)
            if result_data.get("error"):
                logger.warning("extraction_not_invoice", image_index=image_index)
                return ExtractionResult(
                    invoice=ExtractedInvoice(image_index=image_index),
                    products=[],
                    extraction_confidence=0.0,
                    raw_text=result_data.get("error"),
                )

            # Build extraction result
            invoice_data = result_data.get("invoice") or {}
            products_data = result_data.get("products") or []

            # Debug: log products array from Gemini
            logger.debug(
                "products_data_from_gemini",
                image_index=image_index,
                products_count=len(products_data),
                products_preview=products_data[:3] if products_data else [],  # First 3 products
            )

            products = [
                ExtractedProduct(
                    quantity=max(1, int(p.get("quantity", 1))),
                    description=str(p.get("description", "")).strip(),
                    unit_price=max(0, float(p.get("unit_price", 0))),
                    total_price=max(0, float(p.get("total_price", 0))),
                    suggested_category=p.get("suggested_category"),
                )
                for p in products_data
                if str(p.get("description", "")).strip()  # Filter empty/whitespace-only
            ]

            extraction = ExtractionResult(
                invoice=ExtractedInvoice(
                    supplier_name=invoice_data.get("supplier_name"),
                    invoice_number=invoice_data.get("invoice_number"),
                    invoice_date=invoice_data.get("invoice_date"),
                    image_index=image_index,
                ),
                products=products,
                extraction_confidence=min(1.0, max(0.0, float(result_data.get("extraction_confidence", 0.7)))),
                raw_text=result_data.get("raw_text"),
            )

            logger.info(
                "extraction_complete",
                image_index=image_index,
                products_count=len(products),
                confidence=extraction.extraction_confidence,
            )

            return extraction

        except json.JSONDecodeError as e:
            logger.error("extraction_json_error", error=str(e), image_index=image_index)
            raise AIExtractionError(f"Failed to parse AI response: {e}") from e
        except Exception as e:
            logger.error("extraction_error", error=str(e), image_index=image_index)
            raise AIExtractionError(f"Extraction failed: {e}") from e

    async def extract_from_images_batch(
        self,
        images: list[tuple[str, str]],  # List of (base64_data, mime_type)
        categories: list[dict[str, Any]] | None = None,
    ) -> tuple[list[ExtractionResult], int]:
        """Extract products from multiple invoice images.

        Args:
            images: List of (base64_data, mime_type) tuples.
            categories: Optional list of categories for all extractions.

        Returns:
            Tuple of (extraction_results, processing_time_ms).
        """
        start_time = time.time()
        results: list[ExtractionResult] = []

        for idx, (image_data, image_type) in enumerate(images):
            try:
                result = await self.extract_from_image(
                    image_base64=image_data,
                    image_type=image_type,
                    image_index=idx,
                    categories=categories,
                )
                results.append(result)
            except AIExtractionError as e:
                logger.error("batch_extraction_error", image_index=idx, error=str(e))
                # Add empty result for failed image
                results.append(
                    ExtractionResult(
                        invoice=ExtractedInvoice(image_index=idx),
                        products=[],
                        extraction_confidence=0.0,
                        raw_text=f"Error: {e}",
                    )
                )

        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "batch_extraction_complete",
            images_count=len(images),
            total_products=sum(len(r.products) for r in results),
            processing_time_ms=processing_time_ms,
        )

        return results, processing_time_ms

    def match_with_catalog(
        self,
        extractions: list[ExtractionResult],
        existing_products: list[dict],
        existing_categories: list[dict],
    ) -> tuple[list[MatchedProduct], list[DetectedCategory]]:
        """Match extracted products with existing catalog.

        Args:
            extractions: List of extraction results.
            existing_products: List of existing products from catalog.
            existing_categories: List of existing categories.

        Returns:
            Tuple of (matched_products, detected_categories).
        """
        matched_products: list[MatchedProduct] = []
        category_counts: dict[str, DetectedCategory] = {}

        # Build category lookup (case-insensitive)
        category_lookup = {c["name"].lower(): c for c in existing_categories}

        for extraction in extractions:
            for product in extraction.products:
                # Find matches in existing catalog
                matches = self._find_product_matches(product.description, existing_products)

                is_new = not matches or matches[0].confidence == MatchConfidence.NONE

                matched = MatchedProduct(
                    extracted=product,
                    matches=matches[:3],  # Top 3 matches
                    is_new_product=is_new,
                    suggested_name=self._standardize_name(product.description),
                )
                matched_products.append(matched)

                # Track categories
                if product.suggested_category:
                    cat_lower = product.suggested_category.lower()
                    existing_cat = category_lookup.get(cat_lower)

                    if cat_lower not in category_counts:
                        category_counts[cat_lower] = DetectedCategory(
                            name=product.suggested_category,
                            exists_in_catalog=existing_cat is not None,
                            existing_category_id=existing_cat["id"] if existing_cat else None,
                            product_count=0,
                        )
                    category_counts[cat_lower].product_count += 1

        detected_categories = list(category_counts.values())

        logger.info(
            "matching_complete",
            total_products=len(matched_products),
            new_products=sum(1 for m in matched_products if m.is_new_product),
            categories=len(detected_categories),
        )

        return matched_products, detected_categories

    def _find_product_matches(
        self,
        description: str,
        existing_products: list[dict],
    ) -> list[ProductMatch]:
        """Find potential matches for a product description.

        Uses simple substring matching. In production, this would
        use the database's fuzzy search (pg_trgm).

        Args:
            description: Product description to match.
            existing_products: List of existing products.

        Returns:
            List of potential matches sorted by score.
        """
        matches: list[ProductMatch] = []
        desc_lower = description.lower()
        desc_words = set(desc_lower.split())

        for product in existing_products:
            name_lower = product["name"].lower()
            name_words = set(name_lower.split())

            # Simple word overlap similarity
            common_words = desc_words & name_words
            if common_words:
                # Calculate Jaccard-like similarity
                union_words = desc_words | name_words
                score = len(common_words) / len(union_words)

                # Determine confidence level
                if score >= 0.9:
                    confidence = MatchConfidence.HIGH
                elif score >= 0.7:
                    confidence = MatchConfidence.MEDIUM
                elif score >= 0.5:
                    confidence = MatchConfidence.LOW
                else:
                    confidence = MatchConfidence.NONE

                if score >= 0.3:  # Minimum threshold
                    matches.append(
                        ProductMatch(
                            existing_product_id=product["id"],
                            existing_product_name=product["name"],
                            existing_product_sku=product["sku"],
                            similarity_score=score,
                            confidence=confidence,
                        )
                    )

        # Sort by score descending
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches

    def _standardize_name(self, raw_name: str) -> str:
        """Standardize a product name.

        Args:
            raw_name: Raw product name from invoice.

        Returns:
            Standardized product name.
        """
        # Basic standardization: title case, trim
        standardized = raw_name.strip().title()

        # Common replacements for Spanish abbreviations
        replacements = {
            " Gde ": " Grande ",
            " Gde.": " Grande",
            " Peq ": " Pequeño ",
            " Peq.": " Pequeño",
            " Med ": " Mediano ",
            " Med.": " Mediano",
            " Pza ": " Pieza ",
            " Pza.": " Pieza",
            " Unid ": " Unidad ",
            " Unid.": " Unidad",
        }

        for old, new in replacements.items():
            standardized = standardized.replace(old, new)

        return standardized

    async def get_autocomplete_suggestions(
        self,
        partial_text: str,
        context: str | None = None,
        categories: list[dict[str, Any]] | None = None,
        max_suggestions: int = 5,
    ) -> AutocompleteResponse:
        """Get AI autocomplete suggestions for product name/description.

        Args:
            partial_text: Partial product name or description.
            context: Optional additional context.
            categories: Optional list of categories from database.
            max_suggestions: Maximum number of suggestions to return.

        Returns:
            AutocompleteResponse with suggestions.

        Raises:
            AIExtractionError: If suggestion generation fails.
        """
        if not self._is_configured():
            raise AIExtractionError("Gemini API key not configured")

        logger.info(
            "getting_autocomplete",
            partial_text=partial_text,
            categories_count=len(categories) if categories else 0,
        )

        try:
            # Render prompt with categories (uses Jinja2 template)
            prompt = self._template_service.render_autocomplete_prompt(
                partial_text=partial_text,
                categories=categories,
                context=context,
                max_suggestions=max_suggestions,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )

            # Use defensive JSON extraction (same as extraction)
            result_data = extract_json_from_response(response.text.strip())
            suggestions_data = result_data.get("suggestions", [])

            suggestions = [
                AutocompleteSuggestion(
                    name=s.get("name", ""),
                    description=s.get("description", ""),
                    category=s.get("category"),
                )
                for s in suggestions_data[:max_suggestions]
                if s.get("name")
            ]

            logger.info("autocomplete_complete", suggestions_count=len(suggestions))

            return AutocompleteResponse(suggestions=suggestions)

        except Exception as e:
            logger.error("autocomplete_error", error=str(e))
            raise AIExtractionError(f"Autocomplete failed: {e}") from e
