"""
Unit tests for error response schemas.

Tests all error response schema classes for proper validation,
serialization, and backward compatibility with existing error patterns.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.contexts.shared_kernel.middleware.error_handling.error_response import (
    ErrorDetail,
    ErrorResponse,
    ErrorType,
)


class TestErrorType:
    """Test cases for ErrorType enum."""

    def test_error_type_values(self):
        """Test that all error types have correct string values."""
        assert ErrorType.VALIDATION_ERROR == "validation_error"
        assert ErrorType.AUTHENTICATION_ERROR == "authentication_error"
        assert ErrorType.AUTHORIZATION_ERROR == "authorization_error"
        assert ErrorType.NOT_FOUND_ERROR == "not_found_error"
        assert ErrorType.CONFLICT_ERROR == "conflict_error"
        assert ErrorType.BUSINESS_RULE_ERROR == "business_rule_error"
        assert ErrorType.TIMEOUT_ERROR == "timeout_error"
        assert ErrorType.INTERNAL_ERROR == "internal_error"


class TestErrorDetail:
    """Test cases for ErrorDetail class."""

    def test_error_detail_creation_full(self):
        """Test creating ErrorDetail with all fields."""
        detail = ErrorDetail(
            field="email",
            code="invalid_format",
            message="Email format is invalid",
            context={"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
        )

        assert detail.field == "email"
        assert detail.code == "invalid_format"
        assert detail.message == "Email format is invalid"
        assert detail.context is not None
        assert (
            detail.context["pattern"]
            == "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        )

    def test_error_detail_creation_minimal(self):
        """Test creating ErrorDetail with required fields only."""
        detail = ErrorDetail(code="required", message="This field is required")

        assert detail.field is None
        assert detail.code == "required"
        assert detail.message == "This field is required"
        assert detail.context is None

    def test_error_detail_immutable(self):
        """Test that ErrorDetail is immutable."""
        detail = ErrorDetail(code="test", message="test message")

        with pytest.raises(ValidationError):
            detail.code = "changed"


class TestErrorResponse:
    """Test cases for ErrorResponse class."""

    def test_error_response_creation_full(self):
        """Test creating ErrorResponse with all fields."""
        error_details = [
            ErrorDetail(field="name", code="required", message="Name is required"),
            ErrorDetail(field="email", code="invalid", message="Email is invalid"),
        ]

        error = ErrorResponse(
            status_code=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            detail="Multiple validation errors occurred",
            errors=error_details,
            context={"request_id": "req-123"},
            correlation_id="corr-456",
        )

        assert error.status_code == 422
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.message == "Validation failed"
        assert error.detail == "Multiple validation errors occurred"
        assert error.errors == error_details
        assert error.context is not None
        assert error.context["request_id"] == "req-123"
        assert error.correlation_id == "corr-456"
        assert isinstance(error.timestamp, datetime)

    def test_error_response_creation_minimal(self):
        """Test creating ErrorResponse with required fields only."""
        error = ErrorResponse(
            status_code=404,
            error_type=ErrorType.NOT_FOUND_ERROR,
            message="Resource not found",
            detail="The requested resource does not exist",
        )

        assert error.status_code == 404
        assert error.error_type == ErrorType.NOT_FOUND_ERROR
        assert error.message == "Resource not found"
        assert error.detail == "The requested resource does not exist"
        assert error.errors is None
        assert error.context is None
        assert error.correlation_id is None
        assert isinstance(error.timestamp, datetime)

    def test_error_response_invalid_status_code(self):
        """Test ErrorResponse with invalid status code."""
        # Status code too low (< 400)
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(
                status_code=200,
                error_type=ErrorType.INTERNAL_ERROR,
                message="Error",
                detail="Error detail",
            )

        assert exc_info.value is not None
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("status_code",) for error in errors)

        # Status code too high (> 599)
        with pytest.raises(ValidationError):
            ErrorResponse(
                status_code=600,
                error_type=ErrorType.INTERNAL_ERROR,
                message="Error",
                detail="Error detail",
            )

    def test_error_response_immutable(self):
        """Test that ErrorResponse is immutable."""
        error = ErrorResponse(
            status_code=500,
            error_type=ErrorType.INTERNAL_ERROR,
            message="Internal error",
            detail="System error occurred",
        )

        with pytest.raises(ValidationError):
            error.status_code = 404





class TestErrorResponseSerialization:
    """Test cases for error response serialization."""

    def test_error_response_json_serialization(self):
        """Test JSON serialization of error responses."""
        error_details = [
            ErrorDetail(field="name", code="required", message="Name is required")
        ]

        error = ErrorResponse(
            status_code=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            detail="Input validation error",
            errors=error_details,
            context={"field_count": 1},
        )

        # Test model_dump_json()
        json_str = error.model_dump_json()
        assert isinstance(json_str, str)

        # Test model_dump()
        data = error.model_dump()
        assert isinstance(data, dict)
        assert data["status_code"] == 422
        assert data["error_type"] == "validation_error"
        assert data["message"] == "Validation failed"
        assert len(data["errors"]) == 1
        assert data["errors"][0]["field"] == "name"

    def test_error_detail_json_serialization(self):
        """Test JSON serialization of error details."""
        detail = ErrorDetail(
            field="email",
            code="invalid_format",
            message="Invalid email format",
            context={"regex": "test-pattern"},
        )

        data = detail.model_dump()
        assert data["field"] == "email"
        assert data["code"] == "invalid_format"
        assert data["message"] == "Invalid email format"
        assert data["context"]["regex"] == "test-pattern"


class TestErrorResponseUsagePatterns:
    """Test cases for real-world usage patterns."""

    def test_validation_error_with_field_details(self):
        """Test validation error with multiple field details."""
        errors = [
            ErrorDetail(
                field="name", code="required", message="Recipe name is required"
            ),
            ErrorDetail(
                field="ingredients",
                code="min_length",
                message="At least one ingredient required",
            ),
            ErrorDetail(
                field="prep_time",
                code="min_value",
                message="Preparation time must be positive",
            ),
        ]

        error = ErrorResponse(
            status_code=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message="Recipe validation failed",
            detail="Multiple validation errors in recipe data",
            errors=errors,
            context={"total_errors": 3, "validation_stage": "pre_save"},
        )

        assert error.status_code == 422
        assert error.errors is not None
        assert len(error.errors) == 3
        assert error.context is not None
        assert error.context["total_errors"] == 3

        # Verify each error detail
        assert error.errors[0].field == "name"
        assert error.errors[1].field == "ingredients"
        assert error.errors[2].field == "prep_time"
