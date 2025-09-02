"""Unit tests for LambdaHelpers utility class."""

import json
import os
from unittest.mock import patch

import pytest

from src.contexts.shared_kernel.middleware.lambda_helpers import LambdaHelpers


class TestLambdaHelpers:
    """Test LambdaHelpers static utility methods."""

    def test_extract_path_parameter_exists(self):
        """Test extracting existing path parameter."""
        event = {"pathParameters": {"id": "123", "name": "test"}}
        assert LambdaHelpers.extract_path_parameter(event, "id") == "123"
        assert LambdaHelpers.extract_path_parameter(event, "name") == "test"

    def test_extract_path_parameter_missing(self):
        """Test extracting non-existent path parameter."""
        event = {"pathParameters": {"id": "123"}}
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
        event = {"queryStringParameters": {"page": "1", "limit": "10"}}
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
                "categories": ["web", "api"],
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
        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-123"}}}}
        result = LambdaHelpers.extract_user_id(event)
        assert result == "user-123"

    def test_extract_user_id_missing_structure(self):
        """Test extracting user ID when structure is missing."""
        event = {}
        result = LambdaHelpers.extract_user_id(event)
        assert result is None

    def test_extract_user_id_partial_structure(self):
        """Test extracting user ID when some parts of structure are missing."""
        event = {"requestContext": {"authorizer": {}}}
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
            "Not found", status_code=404, error_code="RESOURCE_NOT_FOUND"
        )

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert body["message"] == "Not found"
        assert body["error_code"] == "RESOURCE_NOT_FOUND"

    def test_format_error_response_with_details(self):
        """Test formatting error response with details."""
        details = {"field": "email", "issue": "invalid format"}
        result = LambdaHelpers.format_error_response(
            "Validation failed", status_code=400, details=details
        )

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["message"] == "Validation failed"
        assert body["details"] == details

    def test_format_error_response_custom_cors_headers(self):
        """Test formatting error response with custom CORS headers."""
        custom_headers = {"Access-Control-Allow-Origin": "https://example.com"}
        result = LambdaHelpers.format_error_response(
            "Error", cors_headers=custom_headers
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
            cors_headers=custom_headers,
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
        from src.contexts.shared_kernel.middleware.lambda_helpers import (
            extract_path_parameter,
        )

        event = {"pathParameters": {"id": "123"}}
        result = extract_path_parameter(event, "id")
        assert result == "123"

    def test_extract_user_id_convenience(self):
        """Test convenience function for user ID extraction."""
        from src.contexts.shared_kernel.middleware.lambda_helpers import (
            extract_user_id,
        )

        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-123"}}}}
        result = extract_user_id(event)
        assert result == "user-123"

    def test_base_endpoint_handler_alias(self):
        """Test BaseEndpointHandler alias for backward compatibility."""
        from src.contexts.shared_kernel.middleware.lambda_helpers import (
            BaseEndpointHandler,
        )

        # Should be the same as LambdaHelpers
        assert BaseEndpointHandler is LambdaHelpers


class TestLambdaHelpersUserAuthentication:
    """Test user authentication utility method."""

    @pytest.mark.anyio
    async def test_validate_user_authentication_success_without_user_object(self):
        """Test successful authentication without returning user object."""
        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-123"}}}}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        # Mock IAM provider
        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                return {"statusCode": 200, "body": {"id": user_id, "roles": []}}

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=False
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event, cors_headers, MockIAMProvider, return_user_object=False
            )

        assert isinstance(result, tuple)
        error_response, user_data = result
        assert error_response is None
        assert user_data == "user-123"

    @pytest.mark.anyio
    async def test_validate_user_authentication_success_with_user_object(self):
        """Test successful authentication with user object."""
        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-123"}}}}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        # Mock IAM provider
        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                return {"statusCode": 200, "body": {"id": user_id, "roles": ["admin"]}}

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=False
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event, cors_headers, MockIAMProvider, return_user_object=True
            )

        assert isinstance(result, tuple)
        error_response, user_data = result
        assert error_response is None
        assert user_data == {"id": "user-123", "roles": ["admin"]}

    @pytest.mark.anyio
    async def test_validate_user_authentication_missing_user_id(self):
        """Test authentication failure when user ID is missing."""
        event = {}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                return {"statusCode": 200, "body": {}}

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=False
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event, cors_headers, MockIAMProvider
            )

        assert isinstance(result, dict)
        assert result["statusCode"] == 401
        assert result["headers"] == cors_headers
        assert "User ID not found" in result["body"]

    @pytest.mark.anyio
    async def test_validate_user_authentication_iam_failure(self):
        """Test authentication failure when IAM returns error."""
        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-123"}}}}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        # Mock IAM provider that returns error
        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                return {"statusCode": 403, "body": "Access denied"}

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=False
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event, cors_headers, MockIAMProvider
            )

        assert isinstance(result, dict)
        assert result["statusCode"] == 403
        assert result["headers"] == cors_headers

    @pytest.mark.anyio
    async def test_validate_user_authentication_localstack_without_user_object(self):
        """Test LocalStack environment bypass without user object."""
        event = {"requestContext": {"authorizer": {"claims": {"sub": "dev-user"}}}}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                raise Exception("Should not be called in LocalStack")

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=True
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event, cors_headers, MockIAMProvider, return_user_object=False
            )

        assert isinstance(result, tuple)
        error_response, user_data = result
        assert error_response is None
        assert user_data == "dev-user"

    @pytest.mark.anyio
    async def test_validate_user_authentication_localstack_with_mock_user(self):
        """Test LocalStack environment with mock user object."""
        event = {"requestContext": {"authorizer": {"claims": {"sub": "dev-user"}}}}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        # Mock user class
        class MockUser:
            def __init__(self, id, roles=None):
                self.id = id
                self.roles = roles or frozenset()

        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                raise Exception("Should not be called in LocalStack")

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=True
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event,
                cors_headers,
                MockIAMProvider,
                return_user_object=True,
                mock_user_class=MockUser,
            )

        assert isinstance(result, tuple)
        error_response, user_data = result
        assert error_response is None
        assert isinstance(user_data, MockUser)
        assert user_data.id == "dev-user"
        assert user_data.roles == frozenset()

    @pytest.mark.anyio
    async def test_validate_user_authentication_exception_handling(self):
        """Test exception handling during authentication."""
        event = {"requestContext": {"authorizer": {"claims": {"sub": "user-123"}}}}
        cors_headers = {"Access-Control-Allow-Origin": "*"}

        # Mock IAM provider that raises exception
        class MockIAMProvider:
            @staticmethod
            async def get(user_id):
                raise Exception("Network error")

        with patch.object(
            LambdaHelpers, "is_localstack_environment", return_value=False
        ):
            result = await LambdaHelpers.validate_user_authentication(
                event, cors_headers, MockIAMProvider
            )

        assert isinstance(result, dict)
        assert result["statusCode"] == 500
        assert result["headers"] == cors_headers
        assert "Internal server error" in result["body"]
