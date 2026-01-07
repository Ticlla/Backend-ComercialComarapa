"""AI Extraction Service for invoice images.

This module provides the AIExtractionService class that uses
Google Gemini Flash Vision to extract product information from
handwritten sales invoices.
"""

from __future__ import annotations

import base64
import json
import time

import google.generativeai as genai

from comercial_comarapa.config import settings
from comercial_comarapa.core.exceptions import AIExtractionError
from comercial_comarapa.core.logging import get_logger
from comercial_comarapa.models.import_extraction import (
    AutocompleteResponse,
    AutocompleteSuggestion,
    DetectedCategory,
    ExtractedInvoice,
    ExtractedProduct,
    ExtractionResult,
    MatchConfidence,
    MatchedProduct,
    ProductMatch,
)

logger = get_logger(__name__)

# =============================================================================
# EXTRACTION PROMPT (Spanish-optimized for handwritten invoices)
# =============================================================================

EXTRACTION_PROMPT = """Analiza esta imagen de una nota de venta/factura escrita a mano.

EXTRAE la siguiente información en formato JSON:

{
  "invoice": {
    "supplier_name": "nombre del proveedor si es visible, null si no",
    "invoice_number": "número de factura/nota si es visible, null si no",
    "invoice_date": "fecha si es visible en formato original, null si no"
  },
  "products": [
    {
      "quantity": 1,
      "description": "descripción exacta del producto como está escrita",
      "unit_price": 0.00,
      "total_price": 0.00,
      "suggested_category": "categoría sugerida basada en el producto"
    }
  ],
  "extraction_confidence": 0.85,
  "raw_text": "texto completo extraído de la imagen"
}

INSTRUCCIONES IMPORTANTES:
1. Lee cuidadosamente la escritura a mano, incluso si está borrosa
2. Mantén las descripciones de productos EXACTAMENTE como están escritas
3. Si no puedes leer un número claramente, usa tu mejor estimación
4. Para precios, asume formato boliviano (Bs.) si no hay símbolo
5. Sugiere categorías como: Limpieza, Ferretería, Automotriz, Alimentos, Bebidas, Hogar, Electrónica, Ropa, Papelería, Otros
6. extraction_confidence debe reflejar qué tan legible es la imagen (0-1)
7. Responde SOLO con el JSON, sin texto adicional
8. Si la imagen no es una factura/nota de venta, responde: {"error": "not_an_invoice"}

CATEGORÍAS COMUNES:
- Limpieza: escobas, mopas, detergentes, baldes, basureros
- Ferretería: clavos, tornillos, herramientas, cables
- Automotriz: aceites, filtros, repuestos
- Alimentos: arroz, azúcar, aceite, fideos
- Bebidas: gaseosas, agua, jugos
- Hogar: platos, vasos, sartenes, ollas
- Papelería: cuadernos, lápices, papel
"""

AUTOCOMPLETE_PROMPT = """Eres un asistente para una ferretería/tienda de variedades en Bolivia.

El usuario está escribiendo el nombre de un producto: "{partial_text}"
{context_line}

Genera 3-5 sugerencias de productos que podrían coincidir.

Responde en formato JSON:
{{
  "suggestions": [
    {{
      "name": "Nombre completo estandarizado del producto",
      "description": "Descripción profesional del producto (1-2 oraciones)",
      "category": "Categoría sugerida"
    }}
  ]
}}

INSTRUCCIONES:
1. Los nombres deben ser claros y estandarizados
2. Las descripciones deben ser útiles para el inventario
3. Sugiere productos relevantes para una ferretería/tienda boliviana
4. Responde SOLO con JSON válido
"""


class AIExtractionService:
    """Service for AI-powered product extraction from invoice images.

    Uses Google Gemini Flash Vision to process handwritten invoices
    and extract structured product information.
    """

    def __init__(self) -> None:
        """Initialize the AI extraction service."""
        if not settings.gemini_api_key:
            logger.warning("gemini_api_key_not_configured")
        else:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
            logger.info("ai_extraction_service_initialized", model=settings.gemini_model)

    def _is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(settings.gemini_api_key)

    async def extract_from_image(
        self,
        image_base64: str,
        image_type: str = "image/jpeg",
        image_index: int = 0,
    ) -> ExtractionResult:
        """Extract products from a single invoice image.

        Args:
            image_base64: Base64-encoded image data.
            image_type: MIME type of the image.
            image_index: Index of image in batch.

        Returns:
            ExtractionResult with extracted products and metadata.

        Raises:
            AIExtractionError: If extraction fails.
        """
        if not self._is_configured():
            raise AIExtractionError("Gemini API key not configured")

        logger.info("extracting_from_image", image_index=image_index)

        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Create content for Gemini
            response = self.model.generate_content(
                [
                    EXTRACTION_PROMPT,
                    {"mime_type": image_type, "data": image_data},
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature for accuracy
                ),
            )

            # Parse response
            result_text = response.text.strip()
            result_data = json.loads(result_text)

            # Check for error response
            if "error" in result_data:
                logger.warning("extraction_not_invoice", image_index=image_index)
                return ExtractionResult(
                    invoice=ExtractedInvoice(image_index=image_index),
                    products=[],
                    extraction_confidence=0.0,
                    raw_text=result_data.get("error"),
                )

            # Build extraction result
            invoice_data = result_data.get("invoice", {})
            products_data = result_data.get("products", [])

            products = [
                ExtractedProduct(
                    quantity=max(1, int(p.get("quantity", 1))),
                    description=str(p.get("description", "")).strip(),
                    unit_price=max(0, float(p.get("unit_price", 0))),
                    total_price=max(0, float(p.get("total_price", 0))),
                    suggested_category=p.get("suggested_category"),
                )
                for p in products_data
                if p.get("description")
            ]

            extraction = ExtractionResult(
                invoice=ExtractedInvoice(
                    supplier_name=invoice_data.get("supplier_name"),
                    invoice_number=invoice_data.get("invoice_number"),
                    invoice_date=invoice_data.get("invoice_date"),
                    image_index=image_index,
                ),
                products=products,
                extraction_confidence=min(1.0, max(0.0, float(result_data.get("extraction_confidence", 0.7)))),
                raw_text=result_data.get("raw_text"),
            )

            logger.info(
                "extraction_complete",
                image_index=image_index,
                products_count=len(products),
                confidence=extraction.extraction_confidence,
            )

            return extraction

        except json.JSONDecodeError as e:
            logger.error("extraction_json_error", error=str(e), image_index=image_index)
            raise AIExtractionError(f"Failed to parse AI response: {e}") from e
        except Exception as e:
            logger.error("extraction_error", error=str(e), image_index=image_index)
            raise AIExtractionError(f"Extraction failed: {e}") from e

    async def extract_from_images_batch(
        self,
        images: list[tuple[str, str]],  # List of (base64_data, mime_type)
    ) -> tuple[list[ExtractionResult], int]:
        """Extract products from multiple invoice images.

        Args:
            images: List of (base64_data, mime_type) tuples.

        Returns:
            Tuple of (extraction_results, processing_time_ms).
        """
        start_time = time.time()
        results: list[ExtractionResult] = []

        for idx, (image_data, image_type) in enumerate(images):
            try:
                result = await self.extract_from_image(
                    image_base64=image_data,
                    image_type=image_type,
                    image_index=idx,
                )
                results.append(result)
            except AIExtractionError as e:
                logger.error("batch_extraction_error", image_index=idx, error=str(e))
                # Add empty result for failed image
                results.append(
                    ExtractionResult(
                        invoice=ExtractedInvoice(image_index=idx),
                        products=[],
                        extraction_confidence=0.0,
                        raw_text=f"Error: {e}",
                    )
                )

        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "batch_extraction_complete",
            images_count=len(images),
            total_products=sum(len(r.products) for r in results),
            processing_time_ms=processing_time_ms,
        )

        return results, processing_time_ms

    def match_with_catalog(
        self,
        extractions: list[ExtractionResult],
        existing_products: list[dict],
        existing_categories: list[dict],
    ) -> tuple[list[MatchedProduct], list[DetectedCategory]]:
        """Match extracted products with existing catalog.

        Args:
            extractions: List of extraction results.
            existing_products: List of existing products from catalog.
            existing_categories: List of existing categories.

        Returns:
            Tuple of (matched_products, detected_categories).
        """
        matched_products: list[MatchedProduct] = []
        category_counts: dict[str, DetectedCategory] = {}

        # Build category lookup
        category_lookup = {c["name"].lower(): c for c in existing_categories}

        for extraction in extractions:
            for product in extraction.products:
                # Find matches in existing catalog
                matches = self._find_product_matches(product.description, existing_products)

                is_new = not matches or matches[0].confidence == MatchConfidence.NONE

                matched = MatchedProduct(
                    extracted=product,
                    matches=matches[:3],  # Top 3 matches
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
            "matching_complete",
            total_products=len(matched_products),
            new_products=sum(1 for m in matched_products if m.is_new_product),
            categories=len(detected_categories),
        )

        return matched_products, detected_categories

    def _find_product_matches(
        self,
        description: str,
        existing_products: list[dict],
    ) -> list[ProductMatch]:
        """Find potential matches for a product description.

        Uses simple substring matching. In production, this would
        use the database's fuzzy search (pg_trgm).

        Args:
            description: Product description to match.
            existing_products: List of existing products.

        Returns:
            List of potential matches sorted by score.
        """
        matches: list[ProductMatch] = []
        desc_lower = description.lower()
        desc_words = set(desc_lower.split())

        for product in existing_products:
            name_lower = product["name"].lower()
            name_words = set(name_lower.split())

            # Simple word overlap similarity
            common_words = desc_words & name_words
            if common_words:
                # Calculate Jaccard-like similarity
                union_words = desc_words | name_words
                score = len(common_words) / len(union_words)

                # Determine confidence level
                if score >= 0.9:
                    confidence = MatchConfidence.HIGH
                elif score >= 0.7:
                    confidence = MatchConfidence.MEDIUM
                elif score >= 0.5:
                    confidence = MatchConfidence.LOW
                else:
                    confidence = MatchConfidence.NONE

                if score >= 0.3:  # Minimum threshold
                    matches.append(
                        ProductMatch(
                            existing_product_id=product["id"],
                            existing_product_name=product["name"],
                            existing_product_sku=product["sku"],
                            similarity_score=score,
                            confidence=confidence,
                        )
                    )

        # Sort by score descending
        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches

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
        }

        for old, new in replacements.items():
            standardized = standardized.replace(old, new)

        return standardized

    async def get_autocomplete_suggestions(
        self,
        partial_text: str,
        context: str | None = None,
    ) -> AutocompleteResponse:
        """Get AI autocomplete suggestions for product name/description.

        Args:
            partial_text: Partial product name or description.
            context: Optional additional context.

        Returns:
            AutocompleteResponse with suggestions.

        Raises:
            AIExtractionError: If suggestion generation fails.
        """
        if not self._is_configured():
            raise AIExtractionError("Gemini API key not configured")

        logger.info("getting_autocomplete", partial_text=partial_text)

        try:
            context_line = f"\nContexto adicional: {context}" if context else ""
            prompt = AUTOCOMPLETE_PROMPT.format(
                partial_text=partial_text,
                context_line=context_line,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )

            result_data = json.loads(response.text.strip())
            suggestions_data = result_data.get("suggestions", [])

            suggestions = [
                AutocompleteSuggestion(
                    name=s.get("name", ""),
                    description=s.get("description", ""),
                    category=s.get("category"),
                )
                for s in suggestions_data[:5]
                if s.get("name")
            ]

            logger.info("autocomplete_complete", suggestions_count=len(suggestions))

            return AutocompleteResponse(suggestions=suggestions)

        except Exception as e:
            logger.error("autocomplete_error", error=str(e))
            raise AIExtractionError(f"Autocomplete failed: {e}") from e

