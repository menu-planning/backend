"""
Error response schemas for standardized API error handling across all contexts.

This module provides consistent error response formats that unify the current
error handling patterns used by lambda_exception_handler and other error
handling mechanisms across products_catalog, recipes_catalog, and iam contexts.

Key Features:
- Standardized error response structure with detailed context
- HTTP status code validation for error responses (4xx, 5xx)
- Integration with existing exception patterns
- Support for validation errors, business logic errors, and system errors
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorType(str, Enum):
    """Enumeration of error types for categorization."""

    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    CONFLICT_ERROR = "conflict_error"
    BUSINESS_RULE_ERROR = "business_rule_error"
    TIMEOUT_ERROR = "timeout_error"
    INTERNAL_ERROR = "internal_error"


class ErrorDetail(BaseModel):
    """
    Detailed error information for validation and business rule errors.

    Provides structured error details that can include field-specific
    validation errors or business rule violations.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str | None = Field(
        default=None, description="Field name if error is field-specific"
    )
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    context: dict[str, Any] | None = Field(
        default=None, description="Additional error context"
    )


class ErrorResponse(BaseModel):
    """
    Standardized error response schema for all API endpoints.

    Provides consistent error structure that replaces the current
    ad-hoc error response patterns across endpoints.

    Current patterns it replaces:
    - lambda_exception_handler: {"detail": str(e)}
    - IAM errors: {"message": "error text"}
    - Various status-specific error formats

    Usage:
        # Simple error (current lambda_exception_handler pattern)
        error = ErrorResponse(
            statusCode=404,
            error_type=ErrorType.NOT_FOUND_ERROR,
            message="Recipe not found in database",
            detail="Recipe with id 'uuid-123' does not exist"
        )

        # Validation error with field details
        error = ErrorResponse(
            statusCode=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed for recipe data",
            detail="Multiple validation errors occurred",
            errors=[
                ErrorDetail(
                    field="name",
                    code="required",
                    message="Recipe name is required"
                ),
                ErrorDetail(
                    field="ingredients",
                    code="min_length",
                    message="Recipe must have at least one ingredient"
                )
            ]
        )

        # Business rule error
        error = ErrorResponse(
            statusCode=403,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            message="Insufficient permissions",
            detail="User does not have MANAGE_RECIPES permission",
            context={"required_permission": "MANAGE_RECIPES", "user_id": "uuid-456"}
        )
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_assignment=True)

    status_code: int = Field(..., description="HTTP error status code", ge=400, le=599)
    error_type: ErrorType = Field(..., description="Categorized error type")
    message: str = Field(..., description="High-level error message")
    detail: str = Field(..., description="Detailed error description")
    errors: list[ErrorDetail] | None = Field(
        default=None, description="Specific error details for validation errors"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Additional error context"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the error occurred"
    )
    correlation_id: str | None = Field(
        default=None, description="Request correlation ID for tracking"
    )



