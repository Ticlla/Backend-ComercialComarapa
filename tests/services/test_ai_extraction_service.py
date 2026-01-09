"""Tests for AIExtractionService.

Tests the AI extraction service including:
- JSON parsing helpers (_find_json_end, extract_json_from_response)
- List response unwrapping logic
- Extraction result building

NOTE: All tests use mocks - NO actual Gemini API calls are made.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from comercial_comarapa.services.ai_extraction_service import (
    _find_json_end,
    extract_json_from_response,
)

if TYPE_CHECKING:
    from comercial_comarapa.services.ai_extraction_service import AIExtractionService


# =============================================================================
# Shared fixtures for mocking Gemini API
# =============================================================================


@pytest.fixture
def mock_genai() -> MagicMock:
    """Mock the google.generativeai module to prevent cloud connections."""
    with patch("comercial_comarapa.services.ai_extraction_service.genai") as mock:
        # Mock the GenerativeModel
        mock.GenerativeModel.return_value = MagicMock()
        mock.GenerationConfig = MagicMock()
        yield mock


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock settings to provide fake API key."""
    with patch("comercial_comarapa.services.ai_extraction_service.settings") as mock:
        mock.gemini_api_key = "fake-test-key-no-cloud"
        mock.gemini_model = "gemini-2.0-flash"
        yield mock


@pytest.fixture
def mock_service(
    mock_genai: MagicMock,  # noqa: ARG001
    mock_settings: MagicMock,  # noqa: ARG001
) -> AIExtractionService:
    """Create a fully mocked AIExtractionService - NO cloud connections.

    The mock_genai and mock_settings fixtures must be passed to ensure
    the patches are active when AIExtractionService is instantiated.
    """
    from comercial_comarapa.services.ai_extraction_service import (  # noqa: PLC0415
        AIExtractionService,
    )

    service = AIExtractionService()

    # Mock the template service
    service._template_service = MagicMock()
    service._template_service.render_extraction_prompt = MagicMock(return_value="mocked prompt")
    service._template_service.render_autocomplete_prompt = MagicMock(return_value="mocked prompt")

    return service

# =============================================================================
# Tests for _find_json_end helper
# =============================================================================


class TestFindJsonEnd:
    """Tests for _find_json_end helper function."""

    def test_finds_end_of_simple_object(self) -> None:
        """Test finds closing brace of simple JSON object."""
        text = '{"key": "value"}'
        result = _find_json_end(text)
        assert result == len(text) - 1

    def test_finds_end_of_nested_object(self) -> None:
        """Test finds closing brace of nested JSON object."""
        text = '{"outer": {"inner": "value"}}'
        result = _find_json_end(text)
        assert result == len(text) - 1

    def test_finds_end_with_trailing_garbage(self) -> None:
        """Test finds end when garbage text follows JSON."""
        text = '{"key": "value"} some garbage text here'
        result = _find_json_end(text)
        assert result == 15  # Position of closing }

    def test_handles_escaped_quotes_in_strings(self) -> None:
        """Test correctly handles escaped quotes inside strings."""
        text = '{"key": "value with \\"quotes\\""}'
        result = _find_json_end(text)
        assert result == len(text) - 1

    def test_handles_braces_inside_strings(self) -> None:
        """Test ignores braces inside string values."""
        text = '{"key": "value with { and } braces"}'
        result = _find_json_end(text)
        assert result == len(text) - 1

    def test_returns_none_for_unclosed_object(self) -> None:
        """Test returns None when JSON object is not closed."""
        text = '{"key": "value"'
        result = _find_json_end(text)
        assert result is None

    def test_handles_arrays_inside_object(self) -> None:
        """Test correctly handles arrays inside object."""
        text = '{"products": [{"name": "a"}, {"name": "b"}]}'
        result = _find_json_end(text)
        assert result == len(text) - 1

    def test_handles_newlines_and_whitespace(self) -> None:
        """Test handles multiline JSON with whitespace."""
        text = '{\n  "key": "value",\n  "other": 123\n}'
        result = _find_json_end(text)
        assert result == len(text) - 1

    def test_handles_backslash_in_string(self) -> None:
        """Test handles backslash escapes properly."""
        text = '{"path": "C:\\\\Users\\\\test"}'
        result = _find_json_end(text)
        assert result == len(text) - 1


# =============================================================================
# Tests for extract_json_from_response
# =============================================================================


class TestExtractJsonFromResponse:
    """Tests for extract_json_from_response function."""

    def test_parses_valid_json_directly(self) -> None:
        """Test parses clean valid JSON without modification."""
        text = '{"invoice": {}, "products": [], "extraction_confidence": 0.9}'
        result = extract_json_from_response(text)
        assert result == {"invoice": {}, "products": [], "extraction_confidence": 0.9}

    def test_extracts_json_with_trailing_garbage(self) -> None:
        """Test extracts JSON when garbage text follows."""
        text = '{"key": "value"} Thanks for asking! Here is more text...'
        result = extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_extracts_json_with_hallucinated_text(self) -> None:
        """Test extracts JSON when model hallucinates extra text."""
        # This simulates the actual error we encountered
        json_part = '{"invoice": {"supplier_name": "Test"}, "products": [], "extraction_confidence": 0.8}'
        garbage = ' I also need the list to be in markdown format. Thanks.'
        text = json_part + garbage
        result = extract_json_from_response(text)
        assert result["invoice"]["supplier_name"] == "Test"
        assert result["extraction_confidence"] == 0.8

    def test_handles_whitespace_around_json(self) -> None:
        """Test handles leading/trailing whitespace."""
        text = '  \n  {"key": "value"}  \n  '
        result = extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_parses_complex_nested_structure(self) -> None:
        """Test parses complex nested JSON structure."""
        data = {
            "invoice": {
                "supplier_name": "LUBRICANTES HUARACHI",
                "invoice_number": "001387",
            },
            "products": [
                {"quantity": 1, "description": "Aceite", "unit_price": 50.0, "total_price": 50.0},
                {"quantity": 2, "description": "Filtro", "unit_price": 25.0, "total_price": 50.0},
            ],
            "extraction_confidence": 0.85,
        }
        text = json.dumps(data) + " extra text"
        result = extract_json_from_response(text)
        assert result["invoice"]["supplier_name"] == "LUBRICANTES HUARACHI"
        assert len(result["products"]) == 2

    def test_raises_error_for_invalid_json(self) -> None:
        """Test raises JSONDecodeError for completely invalid JSON."""
        text = "This is not JSON at all"
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response(text)

    def test_raises_error_for_truncated_json(self) -> None:
        """Test raises error for truncated JSON that can't be recovered."""
        # Truncated in the middle of a string value
        text = '{"key": "val'
        with pytest.raises(json.JSONDecodeError):
            extract_json_from_response(text)

    def test_parses_json_array_response(self) -> None:
        """Test parses JSON array response."""
        text = '[{"name": "product1"}, {"name": "product2"}]'
        result = extract_json_from_response(text)
        assert isinstance(result, list)
        assert len(result) == 2


# =============================================================================
# Tests for AIExtractionService list response handling
# =============================================================================


class TestListResponseUnwrapping:
    """Tests for list response unwrapping in extract_from_image.

    All tests use mocked Gemini API - NO actual cloud calls.
    """

    @pytest.mark.asyncio
    async def test_unwraps_single_element_list_with_proper_structure(
        self, mock_service: AIExtractionService
    ) -> None:
        """Test unwraps [{ invoice, products }] to { invoice, products }."""
        # Response wrapped in a list (as Gemini sometimes does)
        wrapped_response = json.dumps(
            [
                {
                    "invoice": {"supplier_name": "Test Supplier"},
                    "products": [
                        {"quantity": 1, "description": "Product A", "unit_price": 10.0, "total_price": 10.0}
                    ],
                    "extraction_confidence": 0.9,
                }
            ]
        )

        mock_response = MagicMock()
        mock_response.text = wrapped_response
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",  # base64 for "test"
            categories=[],
        )

        assert len(result.products) == 1
        assert result.products[0].description == "Product A"
        assert result.invoice.supplier_name == "Test Supplier"

    @pytest.mark.asyncio
    async def test_handles_dict_response_normally(self, mock_service: AIExtractionService) -> None:
        """Test handles normal dict response without unwrapping."""
        normal_response = json.dumps(
            {
                "invoice": {"supplier_name": "Normal Supplier"},
                "products": [
                    {"quantity": 2, "description": "Product B", "unit_price": 20.0, "total_price": 40.0}
                ],
                "extraction_confidence": 0.85,
            }
        )

        mock_response = MagicMock()
        mock_response.text = normal_response
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",
            categories=[],
        )

        assert len(result.products) == 1
        assert result.products[0].description == "Product B"
        assert result.products[0].quantity == 2

    @pytest.mark.asyncio
    async def test_handles_list_of_products_directly(self, mock_service: AIExtractionService) -> None:
        """Test handles list of products (not wrapped extraction result)."""
        # List of products without invoice wrapper
        products_list = json.dumps(
            [
                {"quantity": 1, "description": "Item 1", "unit_price": 5.0, "total_price": 5.0},
                {"quantity": 3, "description": "Item 2", "unit_price": 10.0, "total_price": 30.0},
            ]
        )

        mock_response = MagicMock()
        mock_response.text = products_list
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",
            categories=[],
        )

        # Should treat list as products array with default confidence
        assert result.extraction_confidence == 0.5


# =============================================================================
# Tests for product filtering
# =============================================================================


class TestProductFiltering:
    """Tests for product filtering during extraction.

    All tests use mocked Gemini API - NO actual cloud calls.
    """

    @pytest.mark.asyncio
    async def test_filters_products_without_description(self, mock_service: AIExtractionService) -> None:
        """Test filters out products with empty or missing description."""
        response_data = json.dumps(
            {
                "invoice": {},
                "products": [
                    {"quantity": 1, "description": "Valid Product", "unit_price": 10.0, "total_price": 10.0},
                    {"quantity": 1, "description": "", "unit_price": 5.0, "total_price": 5.0},
                    {"quantity": 1, "unit_price": 15.0, "total_price": 15.0},  # Missing description
                    {"quantity": 1, "description": "   ", "unit_price": 8.0, "total_price": 8.0},  # Whitespace only
                ],
                "extraction_confidence": 0.8,
            }
        )

        mock_response = MagicMock()
        mock_response.text = response_data
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",
            categories=[],
        )

        # Only "Valid Product" should remain
        assert len(result.products) == 1
        assert result.products[0].description == "Valid Product"

    @pytest.mark.asyncio
    async def test_enforces_minimum_quantity(self, mock_service: AIExtractionService) -> None:
        """Test enforces minimum quantity of 1."""
        response_data = json.dumps(
            {
                "invoice": {},
                "products": [
                    {"quantity": 0, "description": "Zero Qty", "unit_price": 10.0, "total_price": 10.0},
                    {"quantity": -5, "description": "Negative Qty", "unit_price": 10.0, "total_price": 10.0},
                ],
                "extraction_confidence": 0.8,
            }
        )

        mock_response = MagicMock()
        mock_response.text = response_data
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",
            categories=[],
        )

        # Both should have quantity = 1 (minimum)
        assert all(p.quantity == 1 for p in result.products)

    @pytest.mark.asyncio
    async def test_enforces_non_negative_prices(self, mock_service: AIExtractionService) -> None:
        """Test enforces non-negative prices."""
        response_data = json.dumps(
            {
                "invoice": {},
                "products": [
                    {"quantity": 1, "description": "Negative Price", "unit_price": -10.0, "total_price": -50.0},
                ],
                "extraction_confidence": 0.8,
            }
        )

        mock_response = MagicMock()
        mock_response.text = response_data
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",
            categories=[],
        )

        assert result.products[0].unit_price == Decimal("0")
        assert result.products[0].total_price == Decimal("0")


# =============================================================================
# Tests for error response handling
# =============================================================================


class TestErrorResponseHandling:
    """Tests for error response handling.

    All tests use mocked Gemini API - NO actual cloud calls.
    """

    @pytest.mark.asyncio
    async def test_handles_error_response_from_model(self, mock_service: AIExtractionService) -> None:
        """Test handles error response indicating not an invoice."""
        response_data = json.dumps({"error": "not_an_invoice"})

        mock_response = MagicMock()
        mock_response.text = response_data
        mock_service.model.generate_content = MagicMock(return_value=mock_response)

        result = await mock_service.extract_from_image(
            image_base64="dGVzdA==",
            categories=[],
        )

        assert result.extraction_confidence == 0.0
        assert len(result.products) == 0
        assert result.raw_text == "not_an_invoice"

