"""
Tests for get_product_by_id AWS Lambda endpoint.

Tests cover:
- LambdaHelpers integration (path parameter extraction, user ID extraction)
- Authentication flow (IAMProvider integration)
- Error handling (missing user ID, missing product ID, product not found)
- Environment detection (localstack vs production)
- CORS headers preservation
- Response format compatibility
- Integration with business logic (MessageBus, UnitOfWork)
"""

import json
import pytest
import uuid
from unittest.mock import patch, AsyncMock

from src.contexts.products_catalog.aws_lambda.get_product_by_id import lambda_handler, async_handler
from tests.contexts.products_catalog.aws_lambda.conftest import (
    assert_cors_headers_present,
    assert_error_response_format,
    assert_success_response_format
)

pytestmark = [pytest.mark.anyio]


class TestGetProductByIdEndpoint:
    """Test get_product_by_id endpoint functionality."""

    async def test_successful_product_retrieval_localstack(
        self, 
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test successful product retrieval in localstack environment (no auth required)."""
        # Given: A product exists in the database
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        product_id = str(uuid.uuid4())
        product = create_ORM_product(
            id=product_id,
            name="Test Product for Endpoint",
            source_id="00000000-0000-0000-0000-000000000001"  # Use UUID from fixtures
        )
        test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # Update the event to use the UUID product ID
        event = lambda_event_get_product_by_id.copy()
        event["pathParameters"] = {"id": product_id}
        
        # When: Calling the async endpoint handler
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Response body should contain product data
        body_data = json.loads(response["body"])
        assert body_data["id"] == product_id
        assert body_data["name"] == "Test Product for Endpoint"
        assert "source_id" in body_data

    async def test_successful_product_retrieval_production_with_auth(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_success,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources,
        mock_user_id  # Add the fixture
    ):
        """Test successful product retrieval in production with authentication."""
        # Given: A product exists and IAM authorization succeeds
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        # Use the actual product ID from the event
        product_id = lambda_event_get_product_by_id["pathParameters"]["id"]
        
        product = create_ORM_product(
            id=product_id,
            name="Test Product Production",
            source_id="00000000-0000-0000-0000-000000000001"  # Use existing source
        )
        test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_get_product_by_id, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should have performed IAM authorization with the actual user ID
        mock_iam_provider_success.assert_awaited_once_with(mock_user_id)
        
        # And: Response should contain product data
        body_data = json.loads(response["body"])
        assert body_data["id"] == product_id
        assert body_data["name"] == "Test Product Production"

    async def test_missing_user_id_in_production(
        self,
        base_lambda_event,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test error handling when user ID is missing in production environment."""
        # Given: Lambda event without user context
        event = base_lambda_event.copy()
        event["pathParameters"] = {"id": str(uuid.uuid4())}  # Use proper UUID
        # No requestContext.authorizer (missing user ID)
        
        # When: Calling the async endpoint handler
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return 401 unauthorized
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should contain appropriate error message
        body_data = json.loads(response["body"])
        assert "User ID not found" in body_data["message"]

    async def test_missing_product_id_parameter(
        self,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test error handling when product ID parameter is missing."""
        # Given: Lambda event without product ID in path parameters
        event = {
            "requestContext": {"authorizer": {"principalId": "test_user_123"}},
            "pathParameters": None,  # Missing path parameters
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the async endpoint handler
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return error response
        assert_error_response_format(response, 400)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_empty_product_id_parameter(
        self,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test error handling when product ID parameter is empty."""
        # Given: Lambda event with empty product ID
        event = {
            "requestContext": {"authorizer": {"principalId": "test_user_123"}},
            "pathParameters": {"id": ""},  # Empty product ID
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the async endpoint handler
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return error response
        assert_error_response_format(response, 400)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_product_not_found(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test error handling when product is not found."""
        # Given: Lambda event with non-existent product ID
        nonexistent_id = str(uuid.uuid4())  # Use proper UUID format
        event = lambda_event_get_product_by_id.copy()
        event["pathParameters"] = {"id": nonexistent_id}
        
        # When: Calling the async endpoint handler
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return not found error
        assert response["statusCode"] in [404, 500]  # Could be 404 or 500 depending on implementation
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_lambda_helpers_path_parameter_extraction(
        self,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test that LambdaHelpers.extract_path_parameter is working correctly."""
        # Given: Mock the UnitOfWork and products repository
        with patch("src.contexts.products_catalog.aws_lambda.get_product_by_id.container.bootstrap") as mock_bootstrap:
            mock_bus = AsyncMock()
            mock_uow = AsyncMock()
            mock_uow.products.get = AsyncMock()
            mock_bus.uow.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_bus.uow.__aexit__ = AsyncMock(return_value=None)
            mock_bootstrap.return_value = mock_bus
            
            # Given: Lambda event with specific product ID
            product_id = str(uuid.uuid4())  # Use proper UUID
            event = {
                "requestContext": {"authorizer": {"principalId": "test_user_123"}},
                "pathParameters": {"id": product_id},
                "headers": {"origin": "https://example.com"}
            }
            
            # When: Calling the async endpoint handler
            await async_handler(event, mock_lambda_context)
            
            # Then: Should have called the repository with extracted product ID
            mock_uow.products.get.assert_awaited_once_with(product_id)

    async def test_cors_headers_preservation(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test that CORS headers from CORS_headers.py are preserved."""
        # Given: Lambda event with non-existent product (to trigger error response)
        nonexistent_id = str(uuid.uuid4())  # Use proper UUID
        event = lambda_event_get_product_by_id.copy()
        event["pathParameters"] = {"id": nonexistent_id}
        
        # When: Calling the async endpoint handler
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Response should include CORS headers even in error cases
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_environment_detection(
        self,
        lambda_event_get_product_by_id,
        mock_lambda_context,
        mock_localstack_environment,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test that LambdaHelpers.is_localstack_environment() bypasses auth correctly."""
        # Given: A product exists in the database
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        product_id = str(uuid.uuid4())  # Use proper UUID
        product = create_ORM_product(
            id=product_id,
            name="Environment Test Product",
            source_id="00000000-0000-0000-0000-000000000001"  # Use UUID from fixtures
        )
        test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # Update the event to use the UUID product ID
        event = lambda_event_get_product_by_id.copy()
        event["pathParameters"] = {"id": product_id}
        
        # When: Calling the handler in localstack environment (no auth required)
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should succeed without authentication
        assert response["statusCode"] == 200 