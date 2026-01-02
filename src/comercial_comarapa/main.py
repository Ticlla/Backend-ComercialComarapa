"""FastAPI application entry point.

This module creates and configures the FastAPI application instance.
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from comercial_comarapa import __version__
from comercial_comarapa.api.v1.router import api_router
from comercial_comarapa.config import settings
from comercial_comarapa.core import register_exception_handlers
from comercial_comarapa.core.logging import configure_logging, get_logger
from comercial_comarapa.db.database import check_db_connection, close_pool

# Configure logging on module load
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        _app: FastAPI application instance (unused but required by lifespan protocol).
    """
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=__version__,
        environment=settings.app_env,
        database_mode=settings.database_mode,
        debug=settings.debug,
    )

    yield

    # Shutdown
    logger.info("application_shutting_down", app_name=settings.app_name)
    if settings.is_local_db:
        close_pool()
        logger.info("database_pool_closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Comercial Comarapa API",
        description="REST API for inventory management system",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all application routes.

    Args:
        app: FastAPI application instance.
    """

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Health check endpoint.

        Returns basic health status of the API and its dependencies.
        """
        db_status = await check_db_connection()

        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": __version__,
            "environment": settings.app_env,
            "database": db_status,
        }

    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": __version__,
            "description": "Comercial Comarapa - Inventory Management REST API",
            "docs": "/docs",
            "health": "/health",
        }

    # API v1 routers
    app.include_router(api_router, prefix="/api/v1")


# Create application instance
app = create_app()

