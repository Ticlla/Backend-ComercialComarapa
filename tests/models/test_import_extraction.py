"""Tests for import extraction models.

Tests Pydantic validation for import-related models.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from comercial_comarapa.models.import_extraction import (
    AutocompleteRequest,
    AutocompleteSuggestion,
    BatchExtractionResponse,
    DetectedCategory,
    ExtractedInvoice,
    ExtractedProduct,
    ExtractionResult,
    ImageExtractionRequest,
    MatchConfidence,
    MatchedProduct,
    ProductMatch,
)


class TestExtractedProduct:
    """Tests for ExtractedProduct model."""

    def test_valid_product(self):
        """Test creating a valid extracted product."""
        product = ExtractedProduct(
            quantity=10,
            description="Mopa colores grande",
            unit_price=Decimal("45.00"),
            total_price=Decimal("450.00"),
            suggested_category="Limpieza",
        )

        assert product.quantity == 10
        assert product.description == "Mopa colores grande"
        assert product.unit_price == Decimal("45.00")
        assert product.total_price == Decimal("450.00")
        assert product.suggested_category == "Limpieza"

    def test_quantity_must_be_positive(self):
        """Test that quantity must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractedProduct(
                quantity=0,
                description="Test product",
                unit_price=Decimal("10.00"),
                total_price=Decimal("0.00"),
            )

        assert "quantity" in str(exc_info.value)

    def test_description_required(self):
        """Test that description is required and not empty."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractedProduct(
                quantity=1,
                description="",
                unit_price=Decimal("10.00"),
                total_price=Decimal("10.00"),
            )

        assert "description" in str(exc_info.value)

    def test_price_cannot_be_negative(self):
        """Test that prices cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractedProduct(
                quantity=1,
                description="Test product",
                unit_price=Decimal("-10.00"),
                total_price=Decimal("10.00"),
            )

        assert "unit_price" in str(exc_info.value)

    def test_suggested_category_optional(self):
        """Test that suggested_category is optional."""
        product = ExtractedProduct(
            quantity=1,
            description="Test product",
            unit_price=Decimal("10.00"),
            total_price=Decimal("10.00"),
        )

        assert product.suggested_category is None


class TestExtractedInvoice:
    """Tests for ExtractedInvoice model."""

    def test_valid_invoice(self):
        """Test creating a valid extracted invoice."""
        invoice = ExtractedInvoice(
            supplier_name="Distribuidora Test",
            invoice_number="000123",
            invoice_date="07/01/2026",
            image_index=0,
        )

        assert invoice.supplier_name == "Distribuidora Test"
        assert invoice.invoice_number == "000123"
        assert invoice.image_index == 0

    def test_all_fields_optional_except_image_index(self):
        """Test that only image_index is required."""
        invoice = ExtractedInvoice(image_index=0)

        assert invoice.supplier_name is None
        assert invoice.invoice_number is None
        assert invoice.invoice_date is None

    def test_image_index_required(self):
        """Test that image_index is required."""
        with pytest.raises(ValidationError):
            ExtractedInvoice()  # Missing image_index


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_valid_extraction_result(self):
        """Test creating a valid extraction result."""
        result = ExtractionResult(
            invoice=ExtractedInvoice(image_index=0),
            products=[
                ExtractedProduct(
                    quantity=1,
                    description="Test",
                    unit_price=Decimal("10.00"),
                    total_price=Decimal("10.00"),
                )
            ],
            extraction_confidence=0.85,
        )

        assert result.extraction_confidence == 0.85
        assert len(result.products) == 1

    def test_confidence_bounds(self):
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            ExtractionResult(
                invoice=ExtractedInvoice(image_index=0),
                products=[],
                extraction_confidence=1.5,  # > 1
            )

        with pytest.raises(ValidationError):
            ExtractionResult(
                invoice=ExtractedInvoice(image_index=0),
                products=[],
                extraction_confidence=-0.1,  # < 0
            )

    def test_empty_products_allowed(self):
        """Test that empty products list is allowed."""
        result = ExtractionResult(
            invoice=ExtractedInvoice(image_index=0),
            products=[],
            extraction_confidence=0.0,
        )

        assert len(result.products) == 0


class TestMatchConfidence:
    """Tests for MatchConfidence enum."""

    def test_confidence_levels(self):
        """Test all confidence levels exist."""
        assert MatchConfidence.HIGH == "high"
        assert MatchConfidence.MEDIUM == "medium"
        assert MatchConfidence.LOW == "low"
        assert MatchConfidence.NONE == "none"


class TestProductMatch:
    """Tests for ProductMatch model."""

    def test_valid_product_match(self):
        """Test creating a valid product match."""
        match = ProductMatch(
            existing_product_id=uuid4(),
            existing_product_name="Mopa Color Grande",
            existing_product_sku="LIM-001",
            similarity_score=0.85,
            confidence=MatchConfidence.HIGH,
        )

        assert match.similarity_score == 0.85
        assert match.confidence == MatchConfidence.HIGH

    def test_similarity_score_bounds(self):
        """Test that similarity_score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            ProductMatch(
                existing_product_id=uuid4(),
                existing_product_name="Test",
                existing_product_sku="TST-001",
                similarity_score=1.5,
                confidence=MatchConfidence.HIGH,
            )


class TestDetectedCategory:
    """Tests for DetectedCategory model."""

    def test_existing_category(self):
        """Test detected category that exists in catalog."""
        cat_id = uuid4()
        category = DetectedCategory(
            name="Limpieza",
            exists_in_catalog=True,
            existing_category_id=cat_id,
            product_count=5,
        )

        assert category.exists_in_catalog is True
        assert category.existing_category_id == cat_id

    def test_new_category(self):
        """Test detected category that doesn't exist."""
        category = DetectedCategory(
            name="Nueva Categoria",
            exists_in_catalog=False,
            product_count=2,
        )

        assert category.exists_in_catalog is False
        assert category.existing_category_id is None


class TestImageExtractionRequest:
    """Tests for ImageExtractionRequest model."""

    def test_valid_request(self):
        """Test creating a valid image extraction request."""
        request = ImageExtractionRequest(
            image_base64="SGVsbG8gV29ybGQ=",
            image_type="image/jpeg",
        )

        assert request.image_base64 == "SGVsbG8gV29ybGQ="
        assert request.image_type == "image/jpeg"

    def test_default_image_type(self):
        """Test default image type is jpeg."""
        request = ImageExtractionRequest(image_base64="SGVsbG8=")

        assert request.image_type == "image/jpeg"


class TestAutocompleteRequest:
    """Tests for AutocompleteRequest model."""

    def test_valid_request(self):
        """Test creating a valid autocomplete request."""
        request = AutocompleteRequest(
            partial_text="Escoba met",
            context="limpieza",
        )

        assert request.partial_text == "Escoba met"
        assert request.context == "limpieza"

    def test_min_length_validation(self):
        """Test that partial_text must be at least 2 characters."""
        with pytest.raises(ValidationError):
            AutocompleteRequest(partial_text="E")

    def test_max_length_validation(self):
        """Test that partial_text cannot exceed 100 characters."""
        with pytest.raises(ValidationError):
            AutocompleteRequest(partial_text="x" * 101)

    def test_context_optional(self):
        """Test that context is optional."""
        request = AutocompleteRequest(partial_text="Escoba")

        assert request.context is None


class TestAutocompleteSuggestion:
    """Tests for AutocompleteSuggestion model."""

    def test_valid_suggestion(self):
        """Test creating a valid autocomplete suggestion."""
        suggestion = AutocompleteSuggestion(
            name="Escoba Metálica Industrial",
            description="Escoba de metal resistente para uso industrial",
            category="Limpieza",
        )

        assert suggestion.name == "Escoba Metálica Industrial"
        assert "metal" in suggestion.description.lower()
        assert suggestion.category == "Limpieza"

    def test_category_optional(self):
        """Test that category is optional."""
        suggestion = AutocompleteSuggestion(
            name="Test Product",
            description="Test description",
        )

        assert suggestion.category is None


class TestBatchExtractionResponse:
    """Tests for BatchExtractionResponse model."""

    def test_valid_batch_response(self):
        """Test creating a valid batch extraction response."""
        response = BatchExtractionResponse(
            extractions=[
                ExtractionResult(
                    invoice=ExtractedInvoice(image_index=0),
                    products=[],
                    extraction_confidence=0.9,
                )
            ],
            matched_products=[],
            detected_categories=[],
            total_products=0,
            total_images_processed=1,
            processing_time_ms=1500,
        )

        assert response.total_images_processed == 1
        assert response.processing_time_ms == 1500
        assert len(response.extractions) == 1


class TestMatchedProduct:
    """Tests for MatchedProduct model."""

    def test_new_product(self):
        """Test matched product marked as new."""
        matched = MatchedProduct(
            extracted=ExtractedProduct(
                quantity=1,
                description="Producto Nuevo",
                unit_price=Decimal("10.00"),
                total_price=Decimal("10.00"),
            ),
            matches=[],
            is_new_product=True,
            suggested_name="Producto Nuevo Estándar",
        )

        assert matched.is_new_product is True
        assert len(matched.matches) == 0

    def test_existing_product_match(self):
        """Test matched product with existing product matches."""
        matched = MatchedProduct(
            extracted=ExtractedProduct(
                quantity=1,
                description="Mopa colores",
                unit_price=Decimal("45.00"),
                total_price=Decimal("45.00"),
            ),
            matches=[
                ProductMatch(
                    existing_product_id=uuid4(),
                    existing_product_name="Mopa Color Grande",
                    existing_product_sku="LIM-001",
                    similarity_score=0.90,
                    confidence=MatchConfidence.HIGH,
                )
            ],
            is_new_product=False,
        )

        assert matched.is_new_product is False
        assert len(matched.matches) == 1
        assert matched.matches[0].confidence == MatchConfidence.HIGH

