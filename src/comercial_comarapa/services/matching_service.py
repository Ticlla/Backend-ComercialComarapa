"""Product Matching Service using database fuzzy search.

This module provides the MatchingService class that uses PostgreSQL's
pg_trgm extension for accurate product matching from invoice extractions.

Includes LRU caching for improved performance on repeated queries.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.models.import_extraction import (
    DetectedCategory,
    ExtractedProduct,
    ExtractionResult,
    MatchConfidence,
    MatchedProduct,
    ProductMatch,
)

if TYPE_CHECKING:
    from comercial_comarapa.core.protocols import DatabaseClientProtocol

logger = get_logger(__name__)

# Module-level cache for product matches (TTL-based via manual invalidation)
_MATCH_CACHE: dict[str, tuple[list[ProductMatch], float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes
_CACHE_MAX_SIZE = 500


def _get_cached_matches(key: str) -> list[ProductMatch] | None:
    """Get cached matches if not expired.

    Args:
        key: Cache key.

    Returns:
        Cached matches or None if not found/expired.
    """
    if key in _MATCH_CACHE:
        matches, timestamp = _MATCH_CACHE[key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            return matches
        # Expired, remove from cache
        del _MATCH_CACHE[key]
    return None


def _set_cached_matches(key: str, matches: list[ProductMatch]) -> None:
    """Cache matches with timestamp.

    Args:
        key: Cache key.
        matches: Matches to cache.
    """
    # Evict oldest entries if cache is full
    if len(_MATCH_CACHE) >= _CACHE_MAX_SIZE:
        oldest_key = min(_MATCH_CACHE.keys(), key=lambda k: _MATCH_CACHE[k][1])
        del _MATCH_CACHE[oldest_key]

    _MATCH_CACHE[key] = (matches, time.time())


def clear_match_cache() -> None:
    """Clear all cached matches. Call after product catalog changes."""
    _MATCH_CACHE.clear()
    logger.info("match_cache_cleared")


class MatchingService:
    """Service for matching extracted products with existing catalog.

    Uses PostgreSQL's pg_trgm extension via search_products_hybrid RPC
    for accurate fuzzy matching that handles:
    - Typos and misspellings
    - Accents (e.g., "papelería" matches "papeleria")
    - Partial matches (e.g., "Escob" matches "Escoba")
    - Word order variations

    Example:
        service = MatchingService(db)
        matches = service.find_matches("basurera max gde", limit=5)
        # Returns matches like "Basurera Máxima Grande" with similarity scores
    """

    def __init__(self, db: DatabaseClientProtocol) -> None:
        """Initialize the matching service.

        Args:
            db: Database client for queries.
        """
        self.db = db
        logger.info("matching_service_initialized")

    def find_matches(
        self,
        description: str,
        limit: int = 5,
        similarity_threshold: float = 0.15,
        use_cache: bool = True,
    ) -> list[ProductMatch]:
        """Find potential product matches using database fuzzy search.

        Uses in-memory caching for improved performance on repeated queries.

        Args:
            description: Product description to match.
            limit: Maximum matches to return.
            similarity_threshold: Minimum similarity score (0-1).
            use_cache: Whether to use cached results (default: True).

        Returns:
            List of ProductMatch sorted by similarity score.
        """
        if not description or not description.strip():
            return []

        # Generate cache key
        cache_key = f"{description.strip().lower()}:{limit}:{similarity_threshold}"

        # Check cache first
        if use_cache:
            cached = _get_cached_matches(cache_key)
            if cached is not None:
                logger.debug("cache_hit", description=description[:30])
                return cached

        try:
            # Call the hybrid search RPC (pg_trgm + FTS)
            result = self.db.rpc(
                "search_products_hybrid",
                {
                    "search_term": description.strip(),
                    "result_limit": limit,
                    "similarity_threshold": similarity_threshold,
                    "is_active_filter": True,
                },
            ).execute()

            matches = []
            for row in result.data or []:
                # Calculate confidence based on similarity
                # The RPC returns results ordered by relevance
                # We estimate similarity from position (first = best match)
                position = len(matches)
                estimated_similarity = max(0.3, 1.0 - (position * 0.15))

                if position == 0:
                    confidence = MatchConfidence.HIGH
                elif position <= 2:
                    confidence = MatchConfidence.MEDIUM
                else:
                    confidence = MatchConfidence.LOW

                matches.append(
                    ProductMatch(
                        existing_product_id=row["id"],
                        existing_product_name=row["name"],
                        existing_product_sku=row["sku"],
                        similarity_score=estimated_similarity,
                        confidence=confidence,
                    )
                )

            # Cache the results
            if use_cache:
                _set_cached_matches(cache_key, matches)

            logger.debug(
                "matches_found",
                description=description[:30],
                matches_count=len(matches),
                cached=False,
            )

            return matches

        except Exception as e:
            logger.error("matching_error", description=description[:30], error=str(e))
            return []

    def match_extraction_results(
        self,
        extractions: list[ExtractionResult],
        existing_categories: list[dict],
    ) -> tuple[list[MatchedProduct], list[DetectedCategory]]:
        """Match all extracted products with existing catalog.

        Args:
            extractions: List of extraction results from AI.
            existing_categories: List of existing categories from DB.

        Returns:
            Tuple of (matched_products, detected_categories).
        """
        matched_products: list[MatchedProduct] = []
        category_counts: dict[str, DetectedCategory] = {}

        # Build category lookup (case-insensitive)
        category_lookup = {c["name"].lower(): c for c in existing_categories}

        for extraction in extractions:
            for product in extraction.products:
                # Find matches using database fuzzy search
                matches = self.find_matches(product.description, limit=3)

                # Determine if this is a new product
                is_new = not matches or matches[0].confidence == MatchConfidence.LOW

                matched = MatchedProduct(
                    extracted=product,
                    matches=matches,
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
            "batch_matching_complete",
            total_products=len(matched_products),
            new_products=sum(1 for m in matched_products if m.is_new_product),
            categories=len(detected_categories),
        )

        return matched_products, detected_categories

    def match_single_product(
        self,
        description: str,
        suggested_category: str | None = None,
    ) -> MatchedProduct:
        """Match a single product description.

        Args:
            description: Product description to match.
            suggested_category: Optional category suggestion.

        Returns:
            MatchedProduct with matches and suggestions.
        """
        matches = self.find_matches(description, limit=5)

        is_new = not matches or matches[0].confidence == MatchConfidence.LOW

        return MatchedProduct(
            extracted=ExtractedProduct(
                quantity=1,
                description=description,
                unit_price=0,
                total_price=0,
                suggested_category=suggested_category,
            ),
            matches=matches,
            is_new_product=is_new,
            suggested_name=self._standardize_name(description),
        )

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
            " Cja ": " Caja ",
            " Cja.": " Caja",
            " Paq ": " Paquete ",
            " Paq.": " Paquete",
        }

        for old, new in replacements.items():
            standardized = standardized.replace(old, new)

        return standardized

