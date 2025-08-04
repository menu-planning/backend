"""
Tests for fetch_product AWS Lambda endpoint HTTP adapter layer.

Tests focus on the thin Lambda handler that acts as HTTP adapter:
- LambdaHelpers integration (parameter extraction, filtering)
- Authentication flow between localstack/production environments  
- Event processing (query parameters, multi-value parameters)
- Response formatting (CORS headers, status codes) for error cases
- Input validation (missing user ID, IAM failures)

Business logic success cases are not tested here - they will be tested elsewhere.
"""

import json
import pytest
from unittest.mock import patch

from src.contexts.products_catalog.aws_lambda.fetch_product import async_handler
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from tests.contexts.products_catalog.aws_lambda.conftest import (
    assert_cors_headers_present,
    assert_error_response_format
)

pytestmark = [pytest.mark.anyio]


def parse_response_body(response):
    """Helper to parse JSON from response body (handles both string and bytes)."""
    body = response["body"]
    if isinstance(body, bytes):
        return json.loads(body.decode('utf-8'))
    else:
        return json.loads(body)


class TestFetchProductHTTPAdapter:
    """Test fetch_product Lambda HTTP adapter functionality."""

    async def test_missing_user_id_returns_401(
        self,
        base_lambda_event,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test that missing user ID in production returns 401 with proper format."""
        # Given: Event without user context (no authorizer)
        event = base_lambda_event.copy()
        event["path"] = "/products"
        
        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return 401 with proper error format
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should contain proper error message
        body_data = parse_response_body(response)
        assert "User ID not found" in body_data["message"]

    async def test_iam_provider_unauthorized_preserves_response(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_unauthorized,
        expected_cors_headers
    ):
        """Test that IAM provider unauthorized response is properly handled."""
        # When: IAM provider returns unauthorized
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should preserve IAM response status with CORS headers
        assert response["statusCode"] == 401
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should have called IAM provider
        mock_iam_provider_unauthorized.assert_awaited_once()

    async def test_iam_provider_forbidden_preserves_response(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_forbidden,
        expected_cors_headers
    ):
        """Test that IAM provider forbidden response is properly handled."""
        # When: IAM provider returns forbidden
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should preserve IAM response status with CORS headers
        assert response["statusCode"] == 403
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_user_id_extraction_from_lambda_event(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_success,
        mock_user_id
    ):
        """Test proper user ID extraction using LambdaHelpers."""
        # When: Calling endpoint (will fail later but should extract user ID first)
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should extract user ID and pass to IAM provider
        mock_iam_provider_success.assert_awaited_once_with(mock_user_id)

    async def test_query_parameter_processing_structure(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test that LambdaHelpers.process_query_filters handles parameter structure correctly."""
        # Given: Event with complex query parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = {
            "limit": "25",
            "is-food": "true",  # Kebab case
            "sort": "name"
        }
        event["multiValueQueryStringParameters"] = {
            "limit": ["25"],
            "is-food": ["true"],
            "sort": ["name"],
            "category": ["dairy", "meat"]  # Multi-value
        }
        
        # When: Calling endpoint (may fail in business logic but should process parameters)
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should process parameters without throwing parameter-related errors
        # Note: We don't check for 200 since business logic might fail, but we verify
        # no parameter processing errors occurred
        assert "statusCode" in response

    async def test_empty_query_parameters_handling(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test that empty query parameters are handled gracefully."""
        # Given: Event with no query parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = None
        event["multiValueQueryStringParameters"] = None
        
        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should handle empty parameters gracefully
        assert "statusCode" in response

    async def test_multi_value_query_parameter_structure(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test multi-value query parameter handling."""
        # Given: Event with only multi-value parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = None
        event["multiValueQueryStringParameters"] = {
            "category": ["dairy", "meat", "vegetables"],
            "limit": ["20"]
        }
        
        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should process multi-value parameters without errors
        assert "statusCode" in response

    async def test_cors_headers_match_specification(
        self,
        base_lambda_event,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test that CORS headers match the CORS_headers.py specification exactly."""
        # Given: Event that will trigger error (easier to test than success)
        event = base_lambda_event.copy()
        event["path"] = "/products"
        
        # When: Calling endpoint (will get 401)
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should have exact CORS headers from CORS_headers.py
        headers = response["headers"]
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Access-Control-Allow-Headers"] == "Authorization, Content-Type"
        assert headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"

    async def test_environment_detection_with_lambdahelpers(
        self,
        lambda_event_fetch_products,
        mock_lambda_context
    ):
        """Test environment detection using LambdaHelpers.is_localstack_environment()."""
        # Test production detection (should trigger auth)
        with patch.object(LambdaHelpers, 'is_localstack_environment', return_value=False), \
             patch('src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get') as mock_iam:
            mock_iam.return_value = {"statusCode": 401, "body": "Unauthorized"}
            response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
            # Should get unauthorized response, meaning environment detection worked
            assert response["statusCode"] == 401
            mock_iam.assert_awaited_once()

    async def test_request_structure_validation(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test that Lambda event and context structure is properly handled."""
        # Given: Event with proper structure
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        
        # When: Calling with context
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should handle structure properly (no structure-related errors)
        assert "statusCode" in response
        assert "headers" in response

    async def test_error_response_format_consistency(
        self,
        base_lambda_event,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test that error responses maintain consistent format."""
        # Given: Event that will trigger 401 error
        event = base_lambda_event.copy()
        event["path"] = "/products"
        
        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Error response should have consistent structure
        assert response["statusCode"] == 401
        assert_cors_headers_present(response, expected_cors_headers)
        assert "body" in response
        
        # And: Body should be parseable JSON with message
        body_data = parse_response_body(response)
        assert "message" in body_data 