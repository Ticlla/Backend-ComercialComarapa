"""Tests for Prompt Template Service.

Tests Jinja2 template rendering for AI prompts.
"""

import pytest

from comercial_comarapa.prompts.template_service import PromptTemplateService, get_template_service


class TestPromptTemplateService:
    """Tests for PromptTemplateService class."""

    @pytest.fixture
    def service(self) -> PromptTemplateService:
        """Create a template service for testing."""
        return PromptTemplateService()

    def test_service_initialization(self, service: PromptTemplateService):
        """Test that service initializes correctly."""
        assert service.templates_dir.exists()
        assert service.env is not None

    def test_get_available_templates(self, service: PromptTemplateService):
        """Test listing available templates."""
        templates = service.get_available_templates()
        assert "extraction.j2" in templates
        assert "autocomplete.j2" in templates

    def test_render_extraction_prompt_without_categories(self, service: PromptTemplateService):
        """Test extraction prompt renders with default categories."""
        prompt = service.render_extraction_prompt()

        assert "Analiza esta imagen" in prompt
        assert "CATEGORÍAS COMUNES:" in prompt
        assert "Limpieza:" in prompt
        assert "Ferretería:" in prompt

    def test_render_extraction_prompt_with_categories(self, service: PromptTemplateService):
        """Test extraction prompt renders with custom categories."""
        categories = [
            {"name": "Lubricantes", "description": "Aceites y grasas"},
            {"name": "Herramientas", "description": "Herramientas manuales"},
        ]
        prompt = service.render_extraction_prompt(categories=categories)

        assert "CATEGORÍAS DISPONIBLES" in prompt
        assert "Lubricantes" in prompt
        assert "Aceites y grasas" in prompt
        assert "Herramientas" in prompt
        # Should NOT have default categories
        assert "CATEGORÍAS COMUNES:" not in prompt

    def test_render_extraction_prompt_with_default_category(self, service: PromptTemplateService):
        """Test extraction prompt uses custom default category."""
        prompt = service.render_extraction_prompt(default_category="Sin Categoría")

        assert "Sin Categoría" in prompt

    def test_render_autocomplete_prompt_basic(self, service: PromptTemplateService):
        """Test autocomplete prompt renders with partial text."""
        prompt = service.render_autocomplete_prompt(partial_text="Escoba met")

        assert "Escoba met" in prompt
        assert "ferretería/tienda de variedades" in prompt
        assert "JSON" in prompt

    def test_render_autocomplete_prompt_with_context(self, service: PromptTemplateService):
        """Test autocomplete prompt includes context."""
        prompt = service.render_autocomplete_prompt(
            partial_text="Aceite",
            context="para motocicleta 4 tiempos",
        )

        assert "Aceite" in prompt
        assert "para motocicleta 4 tiempos" in prompt

    def test_render_autocomplete_prompt_with_categories(self, service: PromptTemplateService):
        """Test autocomplete prompt uses custom categories."""
        categories = [
            {"name": "Lubricantes"},
            {"name": "Filtros"},
        ]
        prompt = service.render_autocomplete_prompt(
            partial_text="Aceite",
            categories=categories,
        )

        assert "CATEGORÍAS DISPONIBLES" in prompt
        assert "Lubricantes" in prompt
        assert "Filtros" in prompt

    def test_render_autocomplete_prompt_max_suggestions(self, service: PromptTemplateService):
        """Test autocomplete prompt respects max_suggestions."""
        prompt = service.render_autocomplete_prompt(
            partial_text="Test",
            max_suggestions=3,
        )

        assert "3 sugerencias" in prompt


class TestGetTemplateService:
    """Tests for get_template_service singleton."""

    def test_returns_same_instance(self):
        """Test that get_template_service returns singleton."""
        service1 = get_template_service()
        service2 = get_template_service()

        assert service1 is service2

    def test_returns_valid_service(self):
        """Test that singleton is properly configured."""
        service = get_template_service()

        assert isinstance(service, PromptTemplateService)
        assert service.templates_dir.exists()






