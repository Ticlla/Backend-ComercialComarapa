"""Tests for Sale models."""

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from comercial_comarapa.models import (
    SaleCancelRequest,
    SaleCreate,
    SaleItemCreate,
    SaleStatus,
)


class TestSaleItemCreate:
    """Tests for SaleItemCreate schema."""

    def test_valid_item(self):
        """Valid sale item."""
        product_id = uuid4()
        item = SaleItemCreate(product_id=product_id, quantity=2)
        assert item.product_id == product_id
        assert item.quantity == 2
        assert item.unit_price is None  # will use product price
        assert item.discount == Decimal("0")

    def test_quantity_required(self):
        """Quantity is required."""
        with pytest.raises(ValidationError) as exc_info:
            SaleItemCreate(product_id=uuid4())
        assert "quantity" in str(exc_info.value)

    def test_quantity_must_be_positive(self):
        """Quantity must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            SaleItemCreate(product_id=uuid4(), quantity=0)
        assert "quantity" in str(exc_info.value)

    def test_with_custom_price(self):
        """Can override unit price."""
        item = SaleItemCreate(
            product_id=uuid4(),
            quantity=1,
            unit_price=99.99,
        )
        assert item.unit_price == Decimal("99.99")

    def test_with_discount(self):
        """Can apply discount."""
        item = SaleItemCreate(
            product_id=uuid4(),
            quantity=1,
            discount=5.00,
        )
        assert item.discount == Decimal("5.00")


class TestSaleCreate:
    """Tests for SaleCreate schema."""

    def test_valid_sale(self):
        """Valid sale with one item."""
        sale = SaleCreate(
            items=[SaleItemCreate(product_id=uuid4(), quantity=1)],
        )
        assert len(sale.items) == 1
        assert sale.discount == Decimal("0")

    def test_items_required(self):
        """Items list is required."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCreate()
        assert "items" in str(exc_info.value)

    def test_at_least_one_item(self):
        """Must have at least one item."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCreate(items=[])
        assert "items" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_multiple_items(self):
        """Can have multiple items."""
        sale = SaleCreate(
            items=[
                SaleItemCreate(product_id=uuid4(), quantity=2),
                SaleItemCreate(product_id=uuid4(), quantity=3),
            ],
        )
        assert len(sale.items) == 2

    def test_with_discount(self):
        """Can apply total discount."""
        sale = SaleCreate(
            items=[SaleItemCreate(product_id=uuid4(), quantity=1)],
            discount=10.00,
        )
        assert sale.discount == Decimal("10.00")

    def test_with_notes(self):
        """Can add notes."""
        sale = SaleCreate(
            items=[SaleItemCreate(product_id=uuid4(), quantity=1)],
            notes="Customer requested gift wrap",
        )
        assert sale.notes == "Customer requested gift wrap"


class TestSaleCancelRequest:
    """Tests for SaleCancelRequest schema."""

    def test_valid_cancel(self):
        """Valid cancellation request."""
        cancel = SaleCancelRequest(reason="Customer changed mind")
        assert cancel.reason == "Customer changed mind"

    def test_reason_required(self):
        """Reason is required."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCancelRequest()
        assert "reason" in str(exc_info.value)

    def test_reason_not_empty(self):
        """Reason cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            SaleCancelRequest(reason="")
        assert "reason" in str(exc_info.value)


class TestSaleStatus:
    """Tests for SaleStatus enum."""

    def test_status_values(self):
        """SaleStatus has expected values."""
        assert SaleStatus.COMPLETED.value == "COMPLETED"
        assert SaleStatus.CANCELLED.value == "CANCELLED"



