"""Prompt Template Service using Jinja2.

This module provides a service for loading and rendering
Jinja2 prompt templates with dynamic context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from comercial_comarapa.core.logging import get_logger

logger = get_logger(__name__)

# Template directory path
TEMPLATES_DIR = Path(__file__).parent / "templates"


class PromptTemplateService:
    """Service for managing and rendering prompt templates.

    Uses Jinja2 to load and render templates with dynamic context,
    enabling flexible prompt generation with real database data.

    Example:
        service = PromptTemplateService()
        categories = [{"name": "Limpieza", "description": "..."}]
        prompt = service.render_extraction_prompt(categories=categories)
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        """Initialize the template service.

        Args:
            templates_dir: Optional custom templates directory.
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info("prompt_template_service_initialized", templates_dir=str(self.templates_dir))

    def render(self, template_name: str, **context: Any) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., "extraction.j2").
            **context: Template variables.

        Returns:
            Rendered template string.
        """
        template = self.env.get_template(template_name)
        rendered = template.render(**context)

        logger.debug(
            "template_rendered",
            template=template_name,
            context_keys=list(context.keys()),
        )

        return rendered

    def render_extraction_prompt(
        self,
        categories: list[dict[str, Any]] | None = None,
        default_category: str = "Otros",
    ) -> str:
        """Render the extraction prompt with categories.

        Args:
            categories: List of category dicts with 'name' and optional 'description'.
            default_category: Default category for unmatched products.

        Returns:
            Rendered extraction prompt.
        """
        return self.render(
            "extraction.j2",
            categories=categories,
            default_category=default_category,
        )

    def render_autocomplete_prompt(
        self,
        partial_text: str,
        categories: list[dict[str, Any]] | None = None,
        context: str | None = None,
        max_suggestions: int = 5,
    ) -> str:
        """Render the autocomplete prompt with context.

        Args:
            partial_text: Partial product name/description.
            categories: List of category dicts with 'name'.
            context: Additional context for suggestions.
            max_suggestions: Maximum number of suggestions.

        Returns:
            Rendered autocomplete prompt.
        """
        return self.render(
            "autocomplete.j2",
            partial_text=partial_text,
            categories=categories,
            context=context,
            max_suggestions=max_suggestions,
        )

    def get_available_templates(self) -> list[str]:
        """List all available template files.

        Returns:
            List of template filenames.
        """
        return [f.name for f in self.templates_dir.glob("*.j2")]


# Singleton instance for easy access
_template_service: PromptTemplateService | None = None


def get_template_service() -> PromptTemplateService:
    """Get the singleton template service instance.

    Returns:
        PromptTemplateService instance.
    """
    global _template_service  # noqa: PLW0603
    if _template_service is None:
        _template_service = PromptTemplateService()
    return _template_service

