"""Tests for Product Import API endpoints.

Tests the import endpoints for AI extraction functionality.
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from comercial_comarapa.api.v1.deps import get_db
from comercial_comarapa.main import app
from comercial_comarapa.models.import_extraction import (
    AutocompleteResponse,
    AutocompleteSuggestion,
    ExtractedInvoice,
    ExtractedProduct,
    ExtractionResult,
)


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_image_base64() -> str:
    """Create a minimal valid JPEG image as base64."""
    # Minimal 1x1 pixel JPEG
    jpeg_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x7E, 0xB4,
        0x01, 0xFF, 0xD9
    ])
    return base64.b64encode(jpeg_bytes).decode("utf-8")


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock database client."""
    mock = MagicMock()
    mock.rpc.return_value.execute.return_value.data = []
    return mock


@pytest.fixture
def mock_extraction_result() -> ExtractionResult:
    """Create a mock extraction result for testing."""
    return ExtractionResult(
        invoice=ExtractedInvoice(
            supplier_name="Distribuidora Test",
            invoice_number="000123",
            invoice_date="07/01/2026",
            image_index=0,
        ),
        products=[
            ExtractedProduct(
                quantity=10,
                description="Mopa colores grande",
                unit_price=45.00,
                total_price=450.00,
                suggested_category="Limpieza",
            ),
            ExtractedProduct(
                quantity=5,
                description="Escoba paja",
                unit_price=25.00,
                total_price=125.00,
                suggested_category="Limpieza",
            ),
        ],
        extraction_confidence=0.92,
        raw_text="Distribuidora Test\nN° 000123\n...",
    )


class TestImportHealthEndpoint:
    """Tests for GET /api/v1/import/health endpoint."""

    def test_health_check_returns_status(self, client: TestClient):
        """Test that health check returns service status."""
        response = client.get("/api/v1/import/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "ai_configured" in data
        assert "max_images_per_batch" in data
        assert "max_image_size_mb" in data
        assert data["max_images_per_batch"] == 20
        assert data["max_image_size_mb"] == 10

    def test_health_check_shows_degraded_without_api_key(self, client: TestClient):
        """Test that health shows degraded when API key is not configured."""
        response = client.get("/api/v1/import/health")

        data = response.json()
        # Without GEMINI_API_KEY, status should be degraded
        if not data["ai_configured"]:
            assert data["status"] == "degraded"
            assert data["ai_model"] is None


class TestExtractFromImageEndpoint:
    """Tests for POST /api/v1/import/extract-from-image endpoint."""

    def test_rejects_invalid_image_type(self, client: TestClient, sample_image_base64: str):
        """Test that invalid image types are rejected."""
        response = client.post(
            "/api/v1/import/extract-from-image",
            json={
                "image_base64": sample_image_base64,
                "image_type": "image/gif",  # Not allowed
            },
        )

        assert response.status_code == 400
        assert "Unsupported image type" in response.json()["detail"]

    def test_rejects_oversized_image(self, client: TestClient):
        """Test that oversized images are rejected."""
        # Create a large base64 string (> 10MB when decoded)
        large_base64 = base64.b64encode(b"x" * (11 * 1024 * 1024)).decode("utf-8")

        response = client.post(
            "/api/v1/import/extract-from-image",
            json={
                "image_base64": large_base64,
                "image_type": "image/jpeg",
            },
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    @patch("comercial_comarapa.api.v1.import_products.CategoryRepository")
    def test_accepts_valid_image_types(
        self,
        mock_category_repo: MagicMock,
        client: TestClient,
        sample_image_base64: str,
    ):
        """Test that valid image types are accepted (validation passes)."""
        # Mock category repository
        mock_repo_instance = MagicMock()
        mock_repo_instance.list.return_value = ([], None)
        mock_category_repo.return_value = mock_repo_instance

        valid_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]

        for image_type in valid_types:
            response = client.post(
                "/api/v1/import/extract-from-image",
                json={
                    "image_base64": sample_image_base64,
                    "image_type": image_type,
                },
            )
            # Should not be 400 for invalid type
            # May be 500 if API key not configured, but not 400 for type
            if response.status_code == 400:
                assert "Unsupported image type" not in response.json().get("detail", "")

    @patch("comercial_comarapa.api.v1.import_products.CategoryRepository")
    @patch("comercial_comarapa.api.v1.import_products.AIExtractionService")
    def test_returns_extraction_result_on_success(
        self,
        mock_service_class: MagicMock,
        mock_category_repo: MagicMock,
        client: TestClient,
        sample_image_base64: str,
        mock_extraction_result: ExtractionResult,
    ):
        """Test successful extraction returns proper response."""
        # Setup category mock
        mock_repo_instance = MagicMock()
        mock_repo_instance.list.return_value = ([], None)
        mock_category_repo.return_value = mock_repo_instance

        # Setup AI service mock
        mock_instance = MagicMock()
        mock_instance._is_configured.return_value = True
        mock_instance.extract_from_image = AsyncMock(return_value=mock_extraction_result)
        mock_service_class.return_value = mock_instance

        response = client.post(
            "/api/v1/import/extract-from-image",
            json={
                "image_base64": sample_image_base64,
                "image_type": "image/jpeg",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "invoice" in data
        assert "products" in data
        assert len(data["products"]) == 2
        assert data["products"][0]["description"] == "Mopa colores grande"


class TestExtractFromImagesEndpoint:
    """Tests for POST /api/v1/import/extract-from-images endpoint."""

    def test_rejects_too_many_images(self, client: TestClient, tmp_path):
        """Test that more than 20 images are rejected."""
        # Create dummy files
        files_list = []
        file_handles = []
        for i in range(21):
            file_path = tmp_path / f"image_{i}.jpg"
            file_path.write_bytes(b"\xff\xd8\xff\xe0" + b"x" * 100)
            f = file_path.open("rb")
            file_handles.append(f)
            files_list.append(("files", (f"image_{i}.jpg", f, "image/jpeg")))

        try:
            response = client.post("/api/v1/import/extract-from-images", files=files_list)
            assert response.status_code == 400
            assert "Too many images" in response.json()["detail"]
        finally:
            for f in file_handles:
                f.close()

    def test_rejects_empty_request(self, client: TestClient):
        """Test that empty request is rejected."""
        response = client.post("/api/v1/import/extract-from-images", files=[])

        # Empty files list results in validation error (422) from FastAPI
        assert response.status_code == 422

    def test_rejects_invalid_file_type(self, client: TestClient, tmp_path):
        """Test that invalid file types are rejected."""
        file_path = tmp_path / "document.pdf"
        file_path.write_bytes(b"%PDF-1.4 test content")

        with file_path.open("rb") as f:
            response = client.post(
                "/api/v1/import/extract-from-images",
                files=[("files", ("document.pdf", f, "application/pdf"))],
            )

        assert response.status_code == 400
        assert "Unsupported type" in response.json()["detail"]


class TestAutocompleteEndpoint:
    """Tests for POST /api/v1/import/autocomplete-product endpoint."""

    def test_rejects_too_short_text(self, client: TestClient):
        """Test that text shorter than 2 chars is rejected."""
        response = client.post(
            "/api/v1/import/autocomplete-product",
            json={"partial_text": "M"},
        )

        assert response.status_code == 422  # Validation error

    @patch("comercial_comarapa.api.v1.import_products.CategoryRepository")
    def test_accepts_valid_request(self, mock_category_repo: MagicMock, client: TestClient):
        """Test that valid request format is accepted."""
        # Mock category repository
        mock_repo_instance = MagicMock()
        mock_repo_instance.list.return_value = ([], None)
        mock_category_repo.return_value = mock_repo_instance

        response = client.post(
            "/api/v1/import/autocomplete-product",
            json={
                "partial_text": "Escoba met",
                "context": "limpieza industrial",
            },
        )

        # Should not be 422 (validation error)
        # May be 500 if API key not configured
        assert response.status_code != 422

    @patch("comercial_comarapa.api.v1.import_products.CategoryRepository")
    @patch("comercial_comarapa.api.v1.import_products.AIExtractionService")
    def test_returns_suggestions_on_success(
        self,
        mock_service_class: MagicMock,
        mock_category_repo: MagicMock,
        client: TestClient,
    ):
        """Test successful autocomplete returns suggestions."""
        # Setup category mock
        mock_repo_instance = MagicMock()
        mock_repo_instance.list.return_value = ([], None)
        mock_category_repo.return_value = mock_repo_instance

        # Setup AI service mock
        mock_instance = MagicMock()
        mock_instance._is_configured.return_value = True
        mock_instance.get_autocomplete_suggestions = AsyncMock(
            return_value=AutocompleteResponse(
                suggestions=[
                    AutocompleteSuggestion(
                        name="Escoba Metálica Industrial",
                        description="Escoba de metal resistente...",
                        category="Limpieza",
                    ),
                    AutocompleteSuggestion(
                        name="Escoba Metálica Grande",
                        description="Escoba con base metálica...",
                        category="Limpieza",
                    ),
                ]
            )
        )
        mock_service_class.return_value = mock_instance

        response = client.post(
            "/api/v1/import/autocomplete-product",
            json={"partial_text": "Escoba met"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["name"] == "Escoba Metálica Industrial"


# =============================================================================
# MATCH PRODUCTS ENDPOINT TESTS
# =============================================================================


class TestMatchProductsEndpoint:
    """Tests for POST /api/v1/import/match-products endpoint."""

    def test_matches_product_description(
        self,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Test returns matches for product description."""
        # Mock the database RPC call
        mock_db.rpc.return_value.execute.return_value.data = [
            {"id": "uuid-1", "name": "Escoba Grande", "sku": "LIM-001"},
        ]

        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            response = client.post(
                "/api/v1/import/match-products",
                json={"description": "escoba grande"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "matched" in data
            assert "processing_time_ms" in data
        finally:
            app.dependency_overrides.clear()

    def test_rejects_empty_description(self, client: TestClient) -> None:
        """Test rejects empty or too short description."""
        response = client.post(
            "/api/v1/import/match-products",
            json={"description": "a"},  # Too short
        )

        assert response.status_code == 422  # Validation error

    def test_includes_suggested_category(
        self,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Test includes suggested category in request."""
        mock_db.rpc.return_value.execute.return_value.data = []

        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            response = client.post(
                "/api/v1/import/match-products",
                json={
                    "description": "producto nuevo",
                    "suggested_category": "Limpieza",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["matched"]["is_new_product"] is True
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# BULK CREATE ENDPOINT TESTS
# =============================================================================


class TestBulkCreateEndpoint:
    """Tests for POST /api/v1/import/bulk-create endpoint."""

    def test_creates_products_successfully(
        self,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Test bulk creates products successfully."""
        from uuid import UUID  # noqa: PLC0415

        # Mock category list
        mock_category = MagicMock()
        mock_category.id = UUID("00000000-0000-0000-0000-000000000001")
        mock_category.name = "Limpieza"

        # Mock product creation
        mock_product = MagicMock()
        mock_product.id = UUID("00000000-0000-0000-0000-000000000002")
        mock_product.sku = "LIM-ABC123"

        with (
            patch(
                "comercial_comarapa.api.v1.import_products.CategoryRepository"
            ) as mock_cat_repo,
            patch(
                "comercial_comarapa.api.v1.import_products.ProductRepository"
            ) as mock_prod_repo,
        ):
            mock_cat_repo.return_value.list.return_value = ([mock_category], 1)
            mock_prod_repo.return_value.create.return_value = mock_product

            app.dependency_overrides[get_db] = lambda: mock_db

            try:
                response = client.post(
                    "/api/v1/import/bulk-create",
                    json={
                        "products": [
                            {
                                "name": "Escoba Grande",
                                "category_name": "Limpieza",
                                "unit_price": 25.00,
                            }
                        ],
                        "create_missing_categories": True,
                    },
                )

                assert response.status_code == 201
                data = response.json()
                assert data["total_requested"] == 1
                assert data["total_created"] == 1
                assert data["total_failed"] == 0
            finally:
                app.dependency_overrides.clear()

    def test_rejects_empty_products_list(self, client: TestClient) -> None:
        """Test rejects empty products list."""
        response = client.post(
            "/api/v1/import/bulk-create",
            json={"products": []},
        )

        assert response.status_code == 422  # Validation error

    def test_handles_creation_errors_gracefully(
        self,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Test handles individual product creation errors."""
        from uuid import UUID  # noqa: PLC0415

        mock_category = MagicMock()
        mock_category.id = UUID("00000000-0000-0000-0000-000000000001")
        mock_category.name = "Limpieza"

        with (
            patch(
                "comercial_comarapa.api.v1.import_products.CategoryRepository"
            ) as mock_cat_repo,
            patch(
                "comercial_comarapa.api.v1.import_products.ProductRepository"
            ) as mock_prod_repo,
        ):
            mock_cat_repo.return_value.list.return_value = ([mock_category], 1)
            mock_prod_repo.return_value.create.side_effect = Exception("DB Error")

            app.dependency_overrides[get_db] = lambda: mock_db

            try:
                response = client.post(
                    "/api/v1/import/bulk-create",
                    json={
                        "products": [
                            {
                                "name": "Producto Fallido",
                                "unit_price": 10.00,
                            }
                        ],
                    },
                )

                assert response.status_code == 201
                data = response.json()
                assert data["total_created"] == 0
                assert data["total_failed"] == 1
                assert data["results"][0]["success"] is False
                assert data["results"][0]["error"] is not None
            finally:
                app.dependency_overrides.clear()

    def test_auto_creates_missing_categories(
        self,
        client: TestClient,
        mock_db: MagicMock,
    ) -> None:
        """Test auto-creates categories when enabled."""
        from uuid import UUID  # noqa: PLC0415

        mock_product = MagicMock()
        mock_product.id = UUID("00000000-0000-0000-0000-000000000002")
        mock_product.sku = "NEW-ABC123"

        mock_new_category = MagicMock()
        mock_new_category.id = UUID("00000000-0000-0000-0000-000000000001")
        mock_new_category.name = "Nueva Categoría"

        with (
            patch(
                "comercial_comarapa.api.v1.import_products.CategoryRepository"
            ) as mock_cat_repo,
            patch(
                "comercial_comarapa.api.v1.import_products.ProductRepository"
            ) as mock_prod_repo,
        ):
            # No existing categories
            mock_cat_repo.return_value.list.return_value = ([], 0)
            mock_cat_repo.return_value.create.return_value = mock_new_category
            mock_prod_repo.return_value.create.return_value = mock_product

            app.dependency_overrides[get_db] = lambda: mock_db

            try:
                response = client.post(
                    "/api/v1/import/bulk-create",
                    json={
                        "products": [
                            {
                                "name": "Producto Nuevo",
                                "category_name": "Nueva Categoría",
                                "unit_price": 50.00,
                            }
                        ],
                        "create_missing_categories": True,
                    },
                )

                assert response.status_code == 201
                data = response.json()
                assert data["categories_created"] == 1
            finally:
                app.dependency_overrides.clear()

