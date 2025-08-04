"""
Unit tests for error response schemas.

Tests all error response schema classes for proper validation,
serialization, and backward compatibility with existing error patterns.
"""

import pytest
from datetime import datetime

from pydantic import ValidationError

from src.contexts.shared_kernel.schemas.error_response import (
    ErrorType,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    ConflictErrorResponse,
    BusinessRuleErrorResponse,
    TimeoutErrorResponse,
    InternalErrorResponse,
    create_detail_error,
    create_message_error
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
            context={"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
        )
        
        assert detail.field == "email"
        assert detail.code == "invalid_format"
        assert detail.message == "Email format is invalid"
        assert detail.context is not None
        assert detail.context["pattern"] == "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    
    def test_error_detail_creation_minimal(self):
        """Test creating ErrorDetail with required fields only."""
        detail = ErrorDetail(
            code="required",
            message="This field is required"
        )
        
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
            ErrorDetail(field="email", code="invalid", message="Email is invalid")
        ]
        
        error = ErrorResponse(
            statusCode=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            detail="Multiple validation errors occurred",
            errors=error_details,
            context={"request_id": "req-123"},
            correlation_id="corr-456"
        )
        
        assert error.statusCode == 422
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
            statusCode=404,
            error_type=ErrorType.NOT_FOUND_ERROR,
            message="Resource not found",
            detail="The requested resource does not exist"
        )
        
        assert error.statusCode == 404
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
                statusCode=200,
                error_type=ErrorType.INTERNAL_ERROR,
                message="Error",
                detail="Error detail"
            )
        
        assert exc_info.value is not None
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("statusCode",) for error in errors)
        
        # Status code too high (> 599)
        with pytest.raises(ValidationError):
            ErrorResponse(
                statusCode=600,
                error_type=ErrorType.INTERNAL_ERROR,
                message="Error",
                detail="Error detail"
            )
    
    def test_error_response_immutable(self):
        """Test that ErrorResponse is immutable."""
        error = ErrorResponse(
            statusCode=500,
            error_type=ErrorType.INTERNAL_ERROR,
            message="Internal error",
            detail="System error occurred"
        )
        
        with pytest.raises(ValidationError):
            error.statusCode = 404

class TestSpecificErrorResponses:
    """Test cases for specific error response classes."""
    
    def test_validation_error_response(self):
        """Test ValidationErrorResponse defaults."""
        error = ValidationErrorResponse(
            message="Validation failed",
            detail="Input validation error"
        )
        
        assert error.statusCode == 422
        assert error.error_type == ErrorType.VALIDATION_ERROR
    
    def test_not_found_error_response(self):
        """Test NotFoundErrorResponse defaults."""
        error = NotFoundErrorResponse(
            message="Resource not found",
            detail="Entity with id 'xyz' not found"
        )
        
        assert error.statusCode == 404
        assert error.error_type == ErrorType.NOT_FOUND_ERROR
    
    def test_authentication_error_response(self):
        """Test AuthenticationErrorResponse defaults."""
        error = AuthenticationErrorResponse(
            message="Authentication failed",
            detail="Invalid credentials provided"
        )
        
        assert error.statusCode == 401
        assert error.error_type == ErrorType.AUTHENTICATION_ERROR
    
    def test_authorization_error_response(self):
        """Test AuthorizationErrorResponse defaults."""
        error = AuthorizationErrorResponse(
            message="Access denied",
            detail="User does not have required permissions"
        )
        
        assert error.statusCode == 403
        assert error.error_type == ErrorType.AUTHORIZATION_ERROR
    
    def test_conflict_error_response(self):
        """Test ConflictErrorResponse defaults."""
        error = ConflictErrorResponse(
            message="Resource conflict",
            detail="Email already exists"
        )
        
        assert error.statusCode == 409
        assert error.error_type == ErrorType.CONFLICT_ERROR
    
    def test_business_rule_error_response(self):
        """Test BusinessRuleErrorResponse defaults."""
        error = BusinessRuleErrorResponse(
            message="Business rule violation",
            detail="Cannot delete recipe with active orders"
        )
        
        assert error.statusCode == 400
        assert error.error_type == ErrorType.BUSINESS_RULE_ERROR
    
    def test_timeout_error_response(self):
        """Test TimeoutErrorResponse defaults."""
        error = TimeoutErrorResponse(
            message="Request timeout",
            detail="Operation timed out after 30 seconds"
        )
        
        assert error.statusCode == 408
        assert error.error_type == ErrorType.TIMEOUT_ERROR
    
    def test_internal_error_response(self):
        """Test InternalErrorResponse defaults."""
        error = InternalErrorResponse(
            message="Internal server error",
            detail="An unexpected error occurred"
        )
        
        assert error.statusCode == 500
        assert error.error_type == ErrorType.INTERNAL_ERROR

class TestBackwardCompatibilityFactories:
    """Test cases for backward compatibility factory functions."""
    
    def test_create_detail_error_basic(self):
        """Test create_detail_error with basic parameters."""
        error = create_detail_error(404, "Entity not found")
        
        assert error.statusCode == 404
        assert error.error_type == ErrorType.NOT_FOUND_ERROR
        assert error.message == "Request failed"
        assert error.detail == "Entity not found"
        assert error.correlation_id is None
    
    def test_create_detail_error_with_correlation_id(self):
        """Test create_detail_error with correlation ID."""
        error = create_detail_error(500, "Internal error", "corr-123")
        
        assert error.statusCode == 500
        assert error.error_type == ErrorType.INTERNAL_ERROR
        assert error.detail == "Internal error"
        assert error.correlation_id == "corr-123"
    
    def test_create_detail_error_status_code_mapping(self):
        """Test create_detail_error status code to error type mapping."""
        test_cases = [
            (400, ErrorType.BUSINESS_RULE_ERROR),
            (401, ErrorType.AUTHENTICATION_ERROR),
            (403, ErrorType.AUTHORIZATION_ERROR),
            (404, ErrorType.NOT_FOUND_ERROR),
            (408, ErrorType.TIMEOUT_ERROR),
            (409, ErrorType.CONFLICT_ERROR),
            (422, ErrorType.VALIDATION_ERROR),
            (500, ErrorType.INTERNAL_ERROR),
            (599, ErrorType.INTERNAL_ERROR),  # Unknown status defaults to internal
        ]
        
        for status_code, expected_type in test_cases:
            error = create_detail_error(status_code, "test error")
            assert error.error_type == expected_type
    
    def test_create_message_error_basic(self):
        """Test create_message_error with basic parameters."""
        error = create_message_error(403, "User does not have enough privileges")
        
        assert error.statusCode == 403
        assert error.error_type == ErrorType.AUTHORIZATION_ERROR
        assert error.message == "User does not have enough privileges"
        assert error.detail == "User does not have enough privileges"  # Same as message
        assert error.correlation_id is None
    
    def test_create_message_error_with_correlation_id(self):
        """Test create_message_error with correlation ID."""
        error = create_message_error(422, "Validation error", "corr-789")
        
        assert error.statusCode == 422
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.message == "Validation error"
        assert error.detail == "Validation error"
        assert error.correlation_id == "corr-789"

class TestErrorResponseSerialization:
    """Test cases for error response serialization."""
    
    def test_error_response_json_serialization(self):
        """Test JSON serialization of error responses."""
        error_details = [
            ErrorDetail(field="name", code="required", message="Name is required")
        ]
        
        error = ErrorResponse(
            statusCode=422,
            error_type=ErrorType.VALIDATION_ERROR,
            message="Validation failed",
            detail="Input validation error",
            errors=error_details,
            context={"field_count": 1}
        )
        
        # Test model_dump_json()
        json_str = error.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test model_dump()
        data = error.model_dump()
        assert isinstance(data, dict)
        assert data["statusCode"] == 422
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
            context={"regex": "test-pattern"}
        )
        
        data = detail.model_dump()
        assert data["field"] == "email"
        assert data["code"] == "invalid_format"
        assert data["message"] == "Invalid email format"
        assert data["context"]["regex"] == "test-pattern"

class TestErrorResponseUsagePatterns:
    """Test cases for real-world usage patterns."""
    
    def test_lambda_exception_handler_pattern(self):
        """Test compatibility with lambda_exception_handler pattern."""
        # Current pattern: {"statusCode": 404, "body": json.dumps({"detail": str(e)})}
        error = create_detail_error(404, "Recipe not found in database")
        
        # This would be the new response structure
        response_dict = {
            "statusCode": error.statusCode,
            "headers": {"Content-Type": "application/json"},
            "body": error.model_dump_json()
        }
        
        assert response_dict["statusCode"] == 404
        assert isinstance(response_dict["body"], str)
        
        # Parse the body to verify structure
        import json
        body_data = json.loads(response_dict["body"])
        assert body_data["detail"] == "Recipe not found in database"
        assert body_data["error_type"] == "not_found_error"
    
    def test_iam_error_pattern(self):
        """Test compatibility with IAM error pattern."""
        # Current pattern: {"message": "error text"}
        error = create_message_error(403, "User does not have enough privileges")
        
        response_dict = {
            "statusCode": error.statusCode,
            "headers": {"Content-Type": "application/json"},
            "body": error.model_dump_json()
        }
        
        assert response_dict["statusCode"] == 403
        
        # Parse the body to verify structure
        import json
        body_data = json.loads(response_dict["body"])
        assert body_data["message"] == "User does not have enough privileges"
        assert body_data["error_type"] == "authorization_error"
    
    def test_validation_error_with_field_details(self):
        """Test validation error with multiple field details."""
        errors = [
            ErrorDetail(field="name", code="required", message="Recipe name is required"),
            ErrorDetail(field="ingredients", code="min_length", message="At least one ingredient required"),
            ErrorDetail(field="prep_time", code="min_value", message="Preparation time must be positive")
        ]
        
        error = ValidationErrorResponse(
            message="Recipe validation failed",
            detail="Multiple validation errors in recipe data",
            errors=errors,
            context={"total_errors": 3, "validation_stage": "pre_save"}
        )
        
        assert error.statusCode == 422
        assert error.errors is not None
        assert len(error.errors) == 3
        assert error.context is not None
        assert error.context["total_errors"] == 3
        
        # Verify each error detail
        assert error.errors[0].field == "name"
        assert error.errors[1].field == "ingredients"
        assert error.errors[2].field == "prep_time" 