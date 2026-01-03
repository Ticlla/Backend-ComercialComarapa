"""Tests for Product models."""

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from comercial_comarapa.models import ProductCreate, ProductFilter, ProductUpdate


class TestProductCreate:
    """Tests for ProductCreate schema."""

    def test_valid_product(self):
        """Valid product creation."""
        product = ProductCreate(
            sku="BEB-001",
            name="Coca Cola 2L",
            unit_price=15.00,
        )
        assert product.sku == "BEB-001"
        assert product.name == "Coca Cola 2L"
        assert product.unit_price == Decimal("15.00")
        assert product.min_stock_level == 5  # default

    def test_sku_required(self):
        """SKU is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="Test", unit_price=10.00)
        assert "sku" in str(exc_info.value)

    def test_name_required(self):
        """Name is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(sku="TEST-001", unit_price=10.00)
        assert "name" in str(exc_info.value)

    def test_unit_price_required(self):
        """Unit price is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(sku="TEST-001", name="Test")
        assert "unit_price" in str(exc_info.value)

    def test_unit_price_non_negative(self):
        """Unit price must be >= 0."""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(sku="TEST-001", name="Test", unit_price=-5.00)
        assert "unit_price" in str(exc_info.value)

    def test_price_decimal_conversion(self):
        """Price is converted to Decimal."""
        product = ProductCreate(sku="TEST", name="Test", unit_price="15.50")
        assert isinstance(product.unit_price, Decimal)
        assert product.unit_price == Decimal("15.50")

    def test_optional_fields(self):
        """Optional fields have correct defaults."""
        product = ProductCreate(sku="TEST", name="Test", unit_price=10)
        assert product.description is None
        assert product.category_id is None
        assert product.cost_price is None
        assert product.min_stock_level == 5

    def test_with_category(self):
        """Can create with category_id."""
        category_id = uuid4()
        product = ProductCreate(
            sku="TEST",
            name="Test",
            unit_price=10,
            category_id=category_id,
        )
        assert product.category_id == category_id


class TestProductUpdate:
    """Tests for ProductUpdate schema."""

    def test_all_fields_optional(self):
        """All fields optional for partial updates."""
        update = ProductUpdate()
        assert update.sku is None
        assert update.name is None
        assert update.unit_price is None

    def test_partial_update_price(self):
        """Can update only price."""
        update = ProductUpdate(unit_price=20.00)
        assert update.unit_price == Decimal("20.00")
        assert update.sku is None

    def test_can_deactivate(self):
        """Can set is_active to False."""
        update = ProductUpdate(is_active=False)
        assert update.is_active is False


class TestProductFilter:
    """Tests for ProductFilter schema."""

    def test_default_values(self):
        """Default filter values."""
        filter_params = ProductFilter()
        assert filter_params.category_id is None
        assert filter_params.is_active is True  # default
        assert filter_params.search is None

    def test_filter_by_category(self):
        """Can filter by category."""
        category_id = uuid4()
        filter_params = ProductFilter(category_id=category_id)
        assert filter_params.category_id == category_id

    def test_filter_by_price_range(self):
        """Can filter by price range."""
        filter_params = ProductFilter(min_price=10, max_price=50)
        assert filter_params.min_price == Decimal("10")
        assert filter_params.max_price == Decimal("50")

    def test_filter_in_stock(self):
        """Can filter by stock availability."""
        filter_params = ProductFilter(in_stock=True)
        assert filter_params.in_stock is True

    def test_search_term(self):
        """Can search by term."""
        filter_params = ProductFilter(search="coca")
        assert filter_params.search == "coca"




