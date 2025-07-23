"""Unit tests for LambdaHelpers utility class."""

import json
import os
from unittest.mock import patch
import pytest

from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers


class TestLambdaHelpers:
    """Test LambdaHelpers static utility methods."""

    def test_extract_path_parameter_exists(self):
        """Test extracting existing path parameter."""
        event = {
            "pathParameters": {
                "id": "123",
                "name": "test"
            }
        }
        assert LambdaHelpers.extract_path_parameter(event, "id") == "123"
        assert LambdaHelpers.extract_path_parameter(event, "name") == "test"

    def test_extract_path_parameter_missing(self):
        """Test extracting non-existent path parameter."""
        event = {
            "pathParameters": {
                "id": "123"
            }
        }
        assert LambdaHelpers.extract_path_parameter(event, "missing") is None

    def test_extract_path_parameter_no_path_params(self):
        """Test extracting path parameter when pathParameters is None."""
        event = {"pathParameters": None}
        assert LambdaHelpers.extract_path_parameter(event, "id") is None

    def test_extract_path_parameter_empty_event(self):
        """Test extracting path parameter from empty event."""
        event = {}
        assert LambdaHelpers.extract_path_parameter(event, "id") is None

    def test_extract_query_parameters_exists(self):
        """Test extracting query parameters when they exist."""
        event = {
            "queryStringParameters": {
                "page": "1",
                "limit": "10"
            }
        }
        result = LambdaHelpers.extract_query_parameters(event)
        assert result == {"page": "1", "limit": "10"}

    def test_extract_query_parameters_none(self):
        """Test extracting query parameters when they are None."""
        event = {"queryStringParameters": None}
        result = LambdaHelpers.extract_query_parameters(event)
        assert result == {}

    def test_extract_query_parameters_missing(self):
        """Test extracting query parameters when key is missing."""
        event = {}
        result = LambdaHelpers.extract_query_parameters(event)
        assert result == {}

    def test_extract_multi_value_query_parameters_exists(self):
        """Test extracting multi-value query parameters when they exist."""
        event = {
            "multiValueQueryStringParameters": {
                "tags": ["python", "lambda"],
                "categories": ["web", "api"]
            }
        }
        result = LambdaHelpers.extract_multi_value_query_parameters(event)
        assert result == {"tags": ["python", "lambda"], "categories": ["web", "api"]}

    def test_extract_multi_value_query_parameters_none(self):
        """Test extracting multi-value query parameters when they are None."""
        event = {"multiValueQueryStringParameters": None}
        result = LambdaHelpers.extract_multi_value_query_parameters(event)
        assert result == {}

    def test_extract_multi_value_query_parameters_missing(self):
        """Test extracting multi-value query parameters when key is missing."""
        event = {}
        result = LambdaHelpers.extract_multi_value_query_parameters(event)
        assert result == {}

    def test_extract_request_body_json_valid(self):
        """Test extracting request body with valid JSON."""
        test_data = {"name": "test", "value": 123}
        event = {"body": json.dumps(test_data)}
        result = LambdaHelpers.extract_request_body(event, parse_json=True)
        assert result == test_data

    def test_extract_request_body_json_invalid(self):
        """Test extracting request body with invalid JSON."""
        event = {"body": "invalid json {"}
        with pytest.raises(ValueError, match="Invalid JSON in request body"):
            LambdaHelpers.extract_request_body(event, parse_json=True)

    def test_extract_request_body_raw_string(self):
        """Test extracting request body as raw string."""
        event = {"body": "raw string content"}
        result = LambdaHelpers.extract_request_body(event, parse_json=False)
        assert result == "raw string content"

    def test_extract_request_body_empty(self):
        """Test extracting empty request body."""
        event = {"body": ""}
        result = LambdaHelpers.extract_request_body(event, parse_json=True)
        assert result == ""

    def test_extract_request_body_none(self):
        """Test extracting request body when body is None."""
        event = {}
        result = LambdaHelpers.extract_request_body(event, parse_json=True)
        assert result == ""

    def test_extract_user_id_valid(self):
        """Test extracting user ID from valid authorizer context."""
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123"
                    }
                }
            }
        }
        result = LambdaHelpers.extract_user_id(event)
        assert result == "user-123"

    def test_extract_user_id_missing_structure(self):
        """Test extracting user ID when structure is missing."""
        event = {}
        result = LambdaHelpers.extract_user_id(event)
        assert result is None

    def test_extract_user_id_partial_structure(self):
        """Test extracting user ID when some parts of structure are missing."""
        event = {
            "requestContext": {
                "authorizer": {}
            }
        }
        result = LambdaHelpers.extract_user_id(event)
        assert result is None

    @patch.dict(os.environ, {"IS_LOCALSTACK": "true"})
    def test_is_localstack_environment_true(self):
        """Test localstack detection when environment variable is true."""
        assert LambdaHelpers.is_localstack_environment() is True

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    def test_is_localstack_environment_false(self):
        """Test localstack detection when environment variable is false."""
        assert LambdaHelpers.is_localstack_environment() is False

    @patch.dict(os.environ, {"IS_LOCALSTACK": "TRUE"})
    def test_is_localstack_environment_case_insensitive(self):
        """Test localstack detection is case insensitive."""
        assert LambdaHelpers.is_localstack_environment() is True

    @patch.dict(os.environ, {}, clear=True)
    def test_is_localstack_environment_missing(self):
        """Test localstack detection when environment variable is missing."""
        assert LambdaHelpers.is_localstack_environment() is False

    def test_get_default_cors_headers(self):
        """Test getting default CORS headers."""
        headers = LambdaHelpers.get_default_cors_headers()
        expected = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        }
        assert headers == expected

    def test_format_error_response_basic(self):
        """Test formatting basic error response."""
        result = LambdaHelpers.format_error_response("Something went wrong")
        
        assert result["statusCode"] == 500
        assert "Access-Control-Allow-Origin" in result["headers"]
        body = json.loads(result["body"])
        assert body["message"] == "Something went wrong"

    def test_format_error_response_with_error_code(self):
        """Test formatting error response with error code."""
        result = LambdaHelpers.format_error_response(
            "Not found", 
            status_code=404,
            error_code="RESOURCE_NOT_FOUND"
        )
        
        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["message"] == "Not found"
        assert body["error_code"] == "RESOURCE_NOT_FOUND"

    def test_format_error_response_with_details(self):
        """Test formatting error response with details."""
        details = {"field": "email", "issue": "invalid format"}
        result = LambdaHelpers.format_error_response(
            "Validation failed",
            status_code=400,
            details=details
        )
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["message"] == "Validation failed"
        assert body["details"] == details

    def test_format_error_response_custom_cors_headers(self):
        """Test formatting error response with custom CORS headers."""
        custom_headers = {"Access-Control-Allow-Origin": "https://example.com"}
        result = LambdaHelpers.format_error_response(
            "Error",
            cors_headers=custom_headers
        )
        
        assert result["headers"] == custom_headers

    def test_format_error_response_all_parameters(self):
        """Test formatting error response with all parameters."""
        details = {"validation": "failed"}
        custom_headers = {"Access-Control-Allow-Origin": "https://example.com"}
        result = LambdaHelpers.format_error_response(
            "Complete error",
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
            cors_headers=custom_headers
        )
        
        assert result["statusCode"] == 422
        assert result["headers"] == custom_headers
        body = json.loads(result["body"])
        assert body["message"] == "Complete error"
        assert body["error_code"] == "VALIDATION_ERROR"
        assert body["details"] == details


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_extract_path_parameter_convenience(self):
        """Test convenience function for path parameter extraction."""
        from src.contexts.shared_kernel.endpoints.base_endpoint_handler import extract_path_parameter
        
        event = {"pathParameters": {"id": "123"}}
        result = extract_path_parameter(event, "id")
        assert result == "123"

    def test_extract_user_id_convenience(self):
        """Test convenience function for user ID extraction."""
        from src.contexts.shared_kernel.endpoints.base_endpoint_handler import extract_user_id
        
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {"sub": "user-123"}
                }
            }
        }
        result = extract_user_id(event)
        assert result == "user-123"

    def test_base_endpoint_handler_alias(self):
        """Test BaseEndpointHandler alias for backward compatibility."""
        from src.contexts.shared_kernel.endpoints.base_endpoint_handler import BaseEndpointHandler
        
        # Should be the same as LambdaHelpers
        assert BaseEndpointHandler is LambdaHelpers 