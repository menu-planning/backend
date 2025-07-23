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

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum

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
    
    model_config = ConfigDict(
        frozen=True,
        extra='forbid'
    )
    
    field: Optional[str] = Field(default=None, description="Field name if error is field-specific")
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")

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
    
    model_config = ConfigDict(
        frozen=True,
        extra='forbid',
        validate_assignment=True
    )
    
    statusCode: int = Field(..., description="HTTP error status code", ge=400, le=599)
    error_type: ErrorType = Field(..., description="Categorized error type")
    message: str = Field(..., description="High-level error message")
    detail: str = Field(..., description="Detailed error description")
    errors: Optional[List[ErrorDetail]] = Field(default=None, description="Specific error details for validation errors")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID for tracking")

# Pre-defined error response classes for common scenarios

class ValidationErrorResponse(ErrorResponse):
    """Validation error response (422 status code)."""
    
    statusCode: int = Field(default=422, description="HTTP validation error status code")
    error_type: ErrorType = Field(default=ErrorType.VALIDATION_ERROR, description="Validation error type")

class NotFoundErrorResponse(ErrorResponse):
    """Not found error response (404 status code)."""
    
    statusCode: int = Field(default=404, description="HTTP not found status code")
    error_type: ErrorType = Field(default=ErrorType.NOT_FOUND_ERROR, description="Not found error type")

class AuthenticationErrorResponse(ErrorResponse):
    """Authentication error response (401 status code)."""
    
    statusCode: int = Field(default=401, description="HTTP authentication error status code")
    error_type: ErrorType = Field(default=ErrorType.AUTHENTICATION_ERROR, description="Authentication error type")

class AuthorizationErrorResponse(ErrorResponse):
    """Authorization error response (403 status code)."""
    
    statusCode: int = Field(default=403, description="HTTP authorization error status code")
    error_type: ErrorType = Field(default=ErrorType.AUTHORIZATION_ERROR, description="Authorization error type")

class ConflictErrorResponse(ErrorResponse):
    """Conflict error response (409 status code)."""
    
    statusCode: int = Field(default=409, description="HTTP conflict status code")
    error_type: ErrorType = Field(default=ErrorType.CONFLICT_ERROR, description="Conflict error type")

class BusinessRuleErrorResponse(ErrorResponse):
    """Business rule violation error response (400 status code)."""
    
    statusCode: int = Field(default=400, description="HTTP bad request status code")
    error_type: ErrorType = Field(default=ErrorType.BUSINESS_RULE_ERROR, description="Business rule error type")

class TimeoutErrorResponse(ErrorResponse):
    """Request timeout error response (408 status code)."""
    
    statusCode: int = Field(default=408, description="HTTP timeout status code")
    error_type: ErrorType = Field(default=ErrorType.TIMEOUT_ERROR, description="Timeout error type")

class InternalErrorResponse(ErrorResponse):
    """Internal server error response (500 status code)."""
    
    statusCode: int = Field(default=500, description="HTTP internal server error status code")
    error_type: ErrorType = Field(default=ErrorType.INTERNAL_ERROR, description="Internal error type")

# Error response factory functions for backward compatibility

def create_detail_error(status_code: int, detail: str, correlation_id: Optional[str] = None) -> ErrorResponse:
    """
    Create error response compatible with current lambda_exception_handler pattern.
    
    This function maintains backward compatibility with the existing pattern:
    {"statusCode": 404, "body": json.dumps({"detail": str(e)})}
    
    Usage:
        error = create_detail_error(404, "Entity not found")
        return {
            "statusCode": error.statusCode,
            "headers": CORS_headers,
            "body": error.model_dump_json()
        }
    """
    error_type_mapping = {
        400: ErrorType.BUSINESS_RULE_ERROR,
        401: ErrorType.AUTHENTICATION_ERROR,
        403: ErrorType.AUTHORIZATION_ERROR,
        404: ErrorType.NOT_FOUND_ERROR,
        408: ErrorType.TIMEOUT_ERROR,
        409: ErrorType.CONFLICT_ERROR,
        422: ErrorType.VALIDATION_ERROR,
        500: ErrorType.INTERNAL_ERROR,
    }
    
    return ErrorResponse(
        statusCode=status_code,
        error_type=error_type_mapping.get(status_code, ErrorType.INTERNAL_ERROR),
        message="Request failed",
        detail=detail,
        correlation_id=correlation_id
    )

def create_message_error(status_code: int, message: str, correlation_id: Optional[str] = None) -> ErrorResponse:
    """
    Create error response compatible with current IAM error pattern.
    
    This function maintains backward compatibility with the existing pattern:
    {"message": "error text"}
    
    Usage:
        error = create_message_error(403, "User does not have enough privileges")
        return {
            "statusCode": error.statusCode,
            "headers": CORS_headers,
            "body": error.model_dump_json()
        }
    """
    error_type_mapping = {
        400: ErrorType.BUSINESS_RULE_ERROR,
        401: ErrorType.AUTHENTICATION_ERROR,
        403: ErrorType.AUTHORIZATION_ERROR,
        404: ErrorType.NOT_FOUND_ERROR,
        408: ErrorType.TIMEOUT_ERROR,
        409: ErrorType.CONFLICT_ERROR,
        422: ErrorType.VALIDATION_ERROR,
        500: ErrorType.INTERNAL_ERROR,
    }
    
    return ErrorResponse(
        statusCode=status_code,
        error_type=error_type_mapping.get(status_code, ErrorType.INTERNAL_ERROR),
        message=message,
        detail=message,  # Use message as detail for backward compatibility
        correlation_id=correlation_id
    ) 