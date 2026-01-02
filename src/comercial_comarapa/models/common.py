"""Common models for API responses and pagination."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# PAGINATION
# =============================================================================


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseModel):
    """Pagination metadata in response."""

    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_items: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")

    @classmethod
    def create(cls, page: int, page_size: int, total_items: int) -> "PaginationMeta":
        """Factory method to create pagination metadata."""
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )


class PaginatedResponse[T](BaseModel):
    """Generic paginated response wrapper."""

    success: bool = True
    data: list[T]
    pagination: PaginationMeta

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# API RESPONSES
# =============================================================================


class APIResponse[T](BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    data: T | None = None
    message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str = Field(description="Error code for client handling")
    message: str = Field(description="Human-readable error message")
    details: list[dict] | None = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: ErrorDetail


# =============================================================================
# MESSAGE RESPONSES
# =============================================================================


class MessageResponse(BaseModel):
    """Simple message response."""

    success: bool = True
    message: str


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    success: bool = True
    message: str = "Resource deleted successfully"
    id: UUID = Field(description="ID of deleted resource")
