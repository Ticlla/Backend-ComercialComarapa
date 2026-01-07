"""Tests for MatchingService.

Tests the database-powered fuzzy matching service using pg_trgm.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from comercial_comarapa.models.import_extraction import (
    ExtractedInvoice,
    ExtractedProduct,
    ExtractionResult,
    MatchConfidence,
)
from comercial_comarapa.services.matching_service import (
    MatchingService,
    clear_match_cache,
)


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Clear matching cache before each test."""
    clear_match_cache()


class TestMatchingServiceInit:
    """Tests for MatchingService initialization."""

    def test_initializes_with_db_client(self) -> None:
        """Test service initializes with database client."""
        mock_db = MagicMock()
        service = MatchingService(mock_db)

        assert service.db == mock_db


class TestFindMatches:
    """Tests for find_matches method."""

    def test_returns_empty_for_empty_description(self) -> None:
        """Test returns empty list for empty description."""
        mock_db = MagicMock()
        service = MatchingService(mock_db)

        result = service.find_matches("")
        assert result == []

        result = service.find_matches("   ")
        assert result == []

    def test_calls_rpc_with_correct_params(self) -> None:
        """Test calls database RPC with correct parameters."""
        mock_db = MagicMock()
        mock_db.rpc.return_value.execute.return_value.data = []

        service = MatchingService(mock_db)
        service.find_matches("escoba", limit=5, similarity_threshold=0.2)

        mock_db.rpc.assert_called_once_with(
            "search_products_hybrid",
            {
                "search_term": "escoba",
                "result_limit": 5,
                "similarity_threshold": 0.2,
                "is_active_filter": True,
            },
        )

    def test_returns_product_matches_from_db_results(self) -> None:
        """Test converts database results to ProductMatch objects."""
        mock_db = MagicMock()
        mock_db.rpc.return_value.execute.return_value.data = [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "Escoba Grande", "sku": "LIM-001"},
            {"id": "00000000-0000-0000-0000-000000000002", "name": "Escoba Mediana", "sku": "LIM-002"},
        ]

        service = MatchingService(mock_db)
        result = service.find_matches("escoba")

        assert len(result) == 2
        assert result[0].existing_product_name == "Escoba Grande"
        assert result[0].existing_product_sku == "LIM-001"
        assert result[0].confidence == MatchConfidence.HIGH
        assert result[1].confidence == MatchConfidence.MEDIUM

    def test_handles_db_error_gracefully(self) -> None:
        """Test returns empty list on database error."""
        mock_db = MagicMock()
        mock_db.rpc.side_effect = Exception("Database error")

        service = MatchingService(mock_db)
        result = service.find_matches("escoba")

        assert result == []


class TestMatchExtractionResults:
    """Tests for match_extraction_results method."""

    def test_matches_products_from_extractions(self) -> None:
        """Test matches products from extraction results."""
        mock_db = MagicMock()
        mock_db.rpc.return_value.execute.return_value.data = [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "Escoba Grande", "sku": "LIM-001"},
        ]

        service = MatchingService(mock_db)

        extractions = [
            ExtractionResult(
                invoice=ExtractedInvoice(image_index=0),
                products=[
                    ExtractedProduct(
                        quantity=1,
                        description="Escoba gde",
                        unit_price=15.0,
                        total_price=15.0,
                        suggested_category="Limpieza",
                    )
                ],
                extraction_confidence=0.9,
            )
        ]

        existing_categories = [{"id": "00000000-0000-0000-0000-000000000010", "name": "Limpieza"}]

        matched_products, detected_categories = service.match_extraction_results(
            extractions, existing_categories
        )

        assert len(matched_products) == 1
        assert matched_products[0].matches[0].existing_product_name == "Escoba Grande"
        assert len(detected_categories) == 1
        assert detected_categories[0].name == "Limpieza"
        assert detected_categories[0].exists_in_catalog is True

    def test_detects_new_categories(self) -> None:
        """Test detects categories that don't exist in catalog."""
        mock_db = MagicMock()
        mock_db.rpc.return_value.execute.return_value.data = []

        service = MatchingService(mock_db)

        extractions = [
            ExtractionResult(
                invoice=ExtractedInvoice(image_index=0),
                products=[
                    ExtractedProduct(
                        quantity=1,
                        description="Producto Nuevo",
                        unit_price=10.0,
                        total_price=10.0,
                        suggested_category="Nueva Categoría",
                    )
                ],
                extraction_confidence=0.9,
            )
        ]

        existing_categories = [{"id": "00000000-0000-0000-0000-000000000010", "name": "Limpieza"}]

        _, detected_categories = service.match_extraction_results(
            extractions, existing_categories
        )

        assert len(detected_categories) == 1
        assert detected_categories[0].name == "Nueva Categoría"
        assert detected_categories[0].exists_in_catalog is False


class TestMatchSingleProduct:
    """Tests for match_single_product method."""

    def test_returns_matched_product(self) -> None:
        """Test returns MatchedProduct for single description."""
        mock_db = MagicMock()
        mock_db.rpc.return_value.execute.return_value.data = [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "Escoba Grande", "sku": "LIM-001"},
        ]

        service = MatchingService(mock_db)
        result = service.match_single_product("escoba grande")

        assert result.is_new_product is False
        assert len(result.matches) > 0

    def test_identifies_new_product_when_no_matches(self) -> None:
        """Test identifies as new product when no matches found."""
        mock_db = MagicMock()
        mock_db.rpc.return_value.execute.return_value.data = []

        service = MatchingService(mock_db)
        result = service.match_single_product("producto inexistente xyz")

        assert result.is_new_product is True
        assert len(result.matches) == 0


class TestStandardizeName:
    """Tests for _standardize_name method."""

    def test_title_cases_name(self) -> None:
        """Test converts to title case."""
        mock_db = MagicMock()
        service = MatchingService(mock_db)

        result = service._standardize_name("escoba grande")
        assert result == "Escoba Grande"

    def test_expands_abbreviations(self) -> None:
        """Test expands common Spanish abbreviations."""
        mock_db = MagicMock()
        service = MatchingService(mock_db)

        result = service._standardize_name("escoba gde.")
        assert "Grande" in result

        result = service._standardize_name("balde peq.")
        assert "Pequeño" in result

