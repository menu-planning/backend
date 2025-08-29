"""
Base response schemas for standardized API responses across all contexts.

This module provides the foundation response schemas that ensure consistent
response formats across products_catalog, recipes_catalog, and iam contexts.

Key Features:
- Standardized HTTP response structure with statusCode, headers, body
- Generic typing for flexible data payloads
- Consistent metadata and pagination support
- Integration with existing CORS headers and custom serializers
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Type variable for generic response data
T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    Base response schema for all API endpoints.

    Provides standardized structure for HTTP responses with:
    - HTTP status code
    - Headers dictionary (for CORS, content-type, etc.)
    - Typed response body
    - Optional metadata

    Usage:
        # For single entity responses
        response = BaseResponse[ApiProduct](
            statusCode=200,
            headers=CORS_headers,
            body=api_product,
            metadata={"processed_at": datetime.now()}
        )

        # For list responses
        response = BaseResponse[list[ApiRecipe]](
            statusCode=200,
            headers=CORS_headers,
            body=recipe_list,
            metadata={"count": len(recipe_list)}
        )
    """

    model_config = ConfigDict(
        frozen=True, extra="forbid", validate_assignment=True, from_attributes=True
    )

    status_code: int = Field(..., description="HTTP status code", ge=100, le=599)
    headers: dict[str, str] = Field(
        default_factory=dict, description="HTTP response headers"
    )
    body: T = Field(..., description="Response payload data")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional response metadata"
    )


class SuccessResponse(BaseResponse[T]):
    """
    Success response schema for successful operations (2xx status codes).

    Extends BaseResponse with success-specific defaults and validation.
    """

    status_code: int = Field(
        default=200, description="HTTP success status code", ge=200, le=299
    )


class CreatedResponse(BaseResponse[T]):
    """
    Created response schema for resource creation (201 status code).

    Used for POST operations that create new resources.
    """

    status_code: int = Field(default=201, description="HTTP created status code")


class NoContentResponse(BaseModel):
    """
    No content response schema for operations that don't return data (204 status code).

    Used for successful operations like DELETE that don't need to return data.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status_code: int = Field(default=204, description="HTTP no content status code")
    headers: dict[str, str] = Field(
        default_factory=dict, description="HTTP response headers"
    )


class CollectionResponse(BaseModel, Generic[T]):
    """
    Collection response schema for paginated list endpoints.

    Provides standardized structure for collection data with pagination metadata.

    Usage:
        collection = CollectionResponse[ApiProduct](
            items=[product1, product2, product3],
            total_count=150,
            page_size=50,
            current_page=1,
            has_next=True,
            has_previous=False
        )

        response = SuccessResponse[CollectionResponse[ApiProduct]](
            statusCode=200,
            headers=CORS_headers,
            body=collection
        )
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_assignment=True)

    items: list[T] = Field(..., description="Collection items")
    total_count: int = Field(..., description="Total number of items available", ge=0)
    page_size: int = Field(..., description="Number of items per page", ge=1)
    current_page: int = Field(default=1, description="Current page number", ge=1)
    has_next: bool = Field(default=False, description="Whether there are more pages")
    has_previous: bool = Field(
        default=False, description="Whether there are previous pages"
    )

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages based on total_count and page_size."""
        if self.total_count == 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size


class MessageResponse(BaseModel):
    """
    Simple message response schema for operations that return status messages.

    Used for operations like creation, updates, or other actions that need
    to communicate success/status but don't return entity data.

    Usage:
        message = MessageResponse(
            message="Recipe created successfully",
            details={"recipe_id": "uuid-string", "status": "published"}
        )

        response = CreatedResponse[MessageResponse](
            statusCode=201,
            headers=CORS_headers,
            body=message
        )
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    message: str = Field(..., description="Success or status message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional details about the operation"
    )


# Convenience type aliases for common response patterns
SuccessMessageResponse = SuccessResponse[MessageResponse]
CreatedMessageResponse = CreatedResponse[MessageResponse]
