"""Tests for Inventory models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from comercial_comarapa.models import (
    MovementReason,
    MovementType,
    StockAdjustmentRequest,
    StockEntryRequest,
    StockExitRequest,
)


class TestStockEntryRequest:
    """Tests for StockEntryRequest schema."""

    def test_valid_entry(self):
        """Valid stock entry."""
        product_id = uuid4()
        entry = StockEntryRequest(product_id=product_id, quantity=50)
        assert entry.product_id == product_id
        assert entry.quantity == 50
        assert entry.reason == MovementReason.PURCHASE  # default

    def test_quantity_required(self):
        """Quantity is required."""
        with pytest.raises(ValidationError) as exc_info:
            StockEntryRequest(product_id=uuid4())
        assert "quantity" in str(exc_info.value)

    def test_quantity_must_be_positive(self):
        """Quantity must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            StockEntryRequest(product_id=uuid4(), quantity=0)
        assert "quantity" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            StockEntryRequest(product_id=uuid4(), quantity=-5)
        assert "quantity" in str(exc_info.value)

    def test_with_reason(self):
        """Can specify reason."""
        entry = StockEntryRequest(
            product_id=uuid4(),
            quantity=10,
            reason=MovementReason.RETURN,
        )
        assert entry.reason == MovementReason.RETURN

    def test_with_notes(self):
        """Can add notes."""
        entry = StockEntryRequest(
            product_id=uuid4(),
            quantity=10,
            notes="Shipment from supplier X",
        )
        assert entry.notes == "Shipment from supplier X"


class TestStockExitRequest:
    """Tests for StockExitRequest schema."""

    def test_valid_exit(self):
        """Valid stock exit."""
        product_id = uuid4()
        exit_req = StockExitRequest(
            product_id=product_id,
            quantity=5,
            reason=MovementReason.DAMAGE,
        )
        assert exit_req.quantity == 5
        assert exit_req.reason == MovementReason.DAMAGE

    def test_reason_required(self):
        """Reason is required for exits."""
        with pytest.raises(ValidationError) as exc_info:
            StockExitRequest(product_id=uuid4(), quantity=5)
        assert "reason" in str(exc_info.value)


class TestStockAdjustmentRequest:
    """Tests for StockAdjustmentRequest schema."""

    def test_valid_adjustment(self):
        """Valid stock adjustment."""
        adjustment = StockAdjustmentRequest(
            product_id=uuid4(),
            new_stock=100,
        )
        assert adjustment.new_stock == 100
        assert adjustment.reason == MovementReason.CORRECTION  # default

    def test_new_stock_can_be_zero(self):
        """New stock can be zero."""
        adjustment = StockAdjustmentRequest(
            product_id=uuid4(),
            new_stock=0,
        )
        assert adjustment.new_stock == 0

    def test_new_stock_cannot_be_negative(self):
        """New stock cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            StockAdjustmentRequest(product_id=uuid4(), new_stock=-10)
        assert "new_stock" in str(exc_info.value)


class TestMovementEnums:
    """Tests for Movement enums."""

    def test_movement_type_values(self):
        """MovementType has expected values."""
        assert MovementType.ENTRY.value == "ENTRY"
        assert MovementType.EXIT.value == "EXIT"
        assert MovementType.ADJUSTMENT.value == "ADJUSTMENT"

    def test_movement_reason_values(self):
        """MovementReason has expected values."""
        assert MovementReason.PURCHASE.value == "PURCHASE"
        assert MovementReason.SALE.value == "SALE"
        assert MovementReason.RETURN.value == "RETURN"
        assert MovementReason.DAMAGE.value == "DAMAGE"
        assert MovementReason.CORRECTION.value == "CORRECTION"
        assert MovementReason.OTHER.value == "OTHER"



