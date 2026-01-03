"""Tests for Category models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from comercial_comarapa.models import CategoryCreate, CategoryResponse, CategoryUpdate


class TestCategoryCreate:
    """Tests for CategoryCreate schema."""

    def test_valid_category(self):
        """Valid category creation."""
        category = CategoryCreate(name="Bebidas", description="Refrescos y jugos")
        assert category.name == "Bebidas"
        assert category.description == "Refrescos y jugos"

    def test_name_required(self):
        """Name is required."""
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(description="Test")
        assert "name" in str(exc_info.value)

    def test_name_min_length(self):
        """Name must have at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(name="")
        assert "name" in str(exc_info.value)

    def test_name_max_length(self):
        """Name max 100 characters."""
        with pytest.raises(ValidationError) as exc_info:
            CategoryCreate(name="x" * 101)
        assert "name" in str(exc_info.value)

    def test_description_optional(self):
        """Description is optional."""
        category = CategoryCreate(name="Bebidas")
        assert category.description is None


class TestCategoryUpdate:
    """Tests for CategoryUpdate schema."""

    def test_all_fields_optional(self):
        """All fields are optional for partial updates."""
        update = CategoryUpdate()
        assert update.name is None
        assert update.description is None

    def test_partial_update_name_only(self):
        """Can update only name."""
        update = CategoryUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.description is None

    def test_partial_update_description_only(self):
        """Can update only description."""
        update = CategoryUpdate(description="New description")
        assert update.name is None
        assert update.description == "New description"


class TestCategoryResponse:
    """Tests for CategoryResponse schema."""

    def test_from_dict(self):
        """Can create from dictionary."""
        data = {
            "id": uuid4(),
            "name": "Bebidas",
            "description": "Test",
            "created_at": "2026-01-02T12:00:00Z",
        }
        response = CategoryResponse(**data)
        assert response.name == "Bebidas"
        assert response.id == data["id"]




