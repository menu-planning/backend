"""
Tests for get_product_by_id AWS Lambda endpoint HTTP adapter layer.

Tests focus on the thin Lambda handler that acts as HTTP adapter:
- LambdaHelpers integration (path parameter extraction, user ID extraction)
- Authentication flow between localstack/production environments
- Path parameter validation and error handling
- Response formatting (CORS headers, status codes) for error cases
- Input validation (missing user ID, missing product ID)

Business logic success cases are not tested here - they will be tested elsewhere.
"""

import json
from unittest.mock import patch

import pytest
from old_tests_v0.contexts.products_catalog.aws_lambda.conftest import (
    assert_cors_headers_present,
    assert_error_response_format,
)
from src.contexts.products_catalog.aws_lambda.get_product_by_id import async_handler
from src.contexts.shared_kernel.middleware.lambda_helpers import LambdaHelpers

pytestmark = [pytest.mark.anyio]


def parse_response_body(response):
    """Helper to parse JSON from response body (handles both string and bytes)."""
    body = response["body"]
    if isinstance(body, bytes):
        return json.loads(body.decode("utf-8"))
    else:
        return json.loads(body)


class TestGetProductByIdHTTPAdapter:
    """Test get_product_by_id Lambda HTTP adapter functionality."""

    async def test_missing_user_id_returns_401(
        self,
        base_lambda_event,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers,
        mock_product_id,
    ):
        """Test that missing user ID in production returns 401 with proper format."""
        # Given: Event without user context but with product ID
        event = base_lambda_event.copy()
        event["path"] = f"/products/{mock_product_id}"
        event["pathParameters"] = {"id": mock_product_id}

        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)

        # Then: Should return 401 with proper error format
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)

        # And: Should contain proper error message
        body_data = parse_response_body(response)
        assert "User ID not found" in body_data["message"]

    async def test_missing_product_id_returns_400(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
    ):
        """Test that missing product ID returns 400 error."""
        # Given: Event without product ID in path parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products/"
        event["pathParameters"] = None  # No product ID

        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)

        # Then: Should return 400 with proper error format
        assert_error_response_format(response, 400)
        assert_cors_headers_present(response, expected_cors_headers)

        # And: Should contain proper error message
        body_data = parse_response_body(response)
        assert "Product ID is required" in body_data["message"]

    async def test_empty_product_id_returns_400(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
    ):
        """Test that empty product ID returns 400 error."""
        # Given: Event with empty product ID
        event = lambda_event_with_user.copy()
        event["path"] = "/products/"
        event["pathParameters"] = {"id": ""}  # Empty product ID

        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)

        # Then: Should return 400 with proper error format
        assert_error_response_format(response, 400)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_user_id_extraction_from_lambda_event(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_success,
        mock_user_id,
    ):
        """Test proper user ID extraction using LambdaHelpers."""
        # When: Calling endpoint (will fail later but should extract user ID first)
        response = await async_handler(
            lambda_event_get_product_by_id, mock_lambda_context
        )

        # Then: Should extract user ID and pass to IAM provider
        mock_iam_provider_success.assert_awaited_once_with(mock_user_id)

    async def test_iam_provider_unauthorized_preserves_response(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_unauthorized,
        expected_cors_headers,
    ):
        """Test that IAM provider unauthorized response is properly handled."""
        # When: IAM provider returns unauthorized
        response = await async_handler(
            lambda_event_get_product_by_id, mock_lambda_context
        )

        # Then: Should preserve IAM response status with CORS headers
        assert response["statusCode"] == 401
        assert_cors_headers_present(response, expected_cors_headers)

        # And: Should have called IAM provider
        mock_iam_provider_unauthorized.assert_awaited_once()

    async def test_iam_provider_forbidden_preserves_response(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_forbidden,
        expected_cors_headers,
    ):
        """Test that IAM provider forbidden response is properly handled."""
        # When: IAM provider returns forbidden
        response = await async_handler(
            lambda_event_get_product_by_id, mock_lambda_context
        )

        # Then: Should preserve IAM response status with CORS headers
        assert response["statusCode"] == 403
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_environment_detection_with_lambdahelpers(
        self, lambda_event_get_product_by_id, mock_lambda_context
    ):
        """Test environment detection using LambdaHelpers.is_localstack_environment()."""
        # Test production detection (requires mocking IAM success)
        with (
            patch.object(
                LambdaHelpers, "is_localstack_environment", return_value=False
            ),
            patch(
                "src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get"
            ) as mock_iam,
        ):
            mock_iam.return_value = {"statusCode": 401, "body": "Unauthorized"}
            response = await async_handler(
                lambda_event_get_product_by_id, mock_lambda_context
            )
            # Should get unauthorized response, meaning environment detection worked
            assert response["statusCode"] == 401

    async def test_path_parameter_extraction_flow(
        self, lambda_event_with_user, mock_lambda_context, mock_localstack_environment
    ):
        """Test that path parameter extraction works (even if business logic fails later)."""
        # Given: Event with valid product ID format
        event = lambda_event_with_user.copy()
        event["pathParameters"] = {"id": "valid-product-id"}

        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)

        # Then: Should pass parameter validation (may fail later in business logic)
        # The fact that we don't get a 400 "Product ID is required" means extraction worked
        assert response[
            "statusCode"
        ] != 400 or "Product ID is required" not in response.get("body", "")

    async def test_cors_headers_in_error_responses(
        self,
        base_lambda_event,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers,
        mock_product_id,
    ):
        """Test that CORS headers are present in error responses."""
        # Given: Event that will trigger 401 error
        event = base_lambda_event.copy()
        event["pathParameters"] = {"id": mock_product_id}

        # When: Calling endpoint
        response = await async_handler(event, mock_lambda_context)

        # Then: Error response should have CORS headers
        assert response["statusCode"] == 401
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_request_context_structure_handling(
        self, lambda_event_with_user, mock_lambda_context, mock_localstack_environment
    ):
        """Test that Lambda context and event structure is properly handled."""
        # Given: Event with proper structure
        event = lambda_event_with_user.copy()
        event["pathParameters"] = {"id": "test-id"}

        # When: Calling with context
        response = await async_handler(event, mock_lambda_context)

        # Then: Should handle context properly (structure validation passes)
        assert "statusCode" in response
        assert "headers" in response
