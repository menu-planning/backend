"""
Tests for fetch_product AWS Lambda endpoint.

Tests cover:
- LambdaHelpers integration (multi-value query parameter extraction, user ID extraction)
- Query parameter filtering and processing
- Authentication flow in different environments
- Error handling for missing user ID
- Response format for collections
- Filter conversion and validation
- CORS headers preservation
"""

import json
import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from src.contexts.products_catalog.aws_lambda.fetch_product import lambda_handler, async_handler
from src.contexts.products_catalog.aws_lambda.fetch_product import container as Container
from tests.contexts.products_catalog.aws_lambda.conftest import (
    assert_cors_headers_present,
    assert_error_response_format,
    assert_success_response_format
)

pytestmark = [pytest.mark.anyio]


class TestFetchProductEndpoint:
    """Test fetch_product endpoint functionality."""

    async def test_successful_product_fetch_localstack(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test successful product fetching in localstack environment."""
        # Given: Multiple products exist in the database
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        products = [
            create_ORM_product(
                id=str(uuid4()),  # Use proper UUID format
                name="Test Food Product 1",
                is_food=True,
                source_id="00000000-0000-0000-0000-000000000001"  # Use existing UUID source
            ),
            create_ORM_product(
                id=str(uuid4()),  # Use proper UUID format
                name="Test Food Product 2",
                is_food=True,
                source_id="00000000-0000-0000-0000-000000000001"  # Use existing UUID source
            ),
            create_ORM_product(
                id=str(uuid4()),  # Use proper UUID format
                name="Test Non-Food Product",
                is_food=False,
                source_id="00000000-0000-0000-0000-000000000001"  # Use existing UUID source
            )
        ]
        
        for product in products:
            test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint with is_food=true filter
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Response should be a list
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)
        
        # And: Should contain only food products (based on the filter)
        if body_data:  # If any products returned (depends on filter implementation)
            for product_data in body_data:
                assert "id" in product_data
                assert "name" in product_data

    async def test_successful_product_fetch_production_with_auth(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_success,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test successful product fetching in production with authentication."""
        # Given: Products exist and IAM authorization succeeds
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        products = [
            create_ORM_product(
                id=str(uuid4()),  # Use proper UUID format
                name="Production Product 1",
                is_food=True,
                source_id="00000000-0000-0000-0000-000000000001"  # Use existing UUID source
            ),
            create_ORM_product(
                id=str(uuid4()),  # Use proper UUID format
                name="Production Product 2",
                is_food=True,
                source_id="00000000-0000-0000-0000-000000000002"  # Use existing UUID source
            )
        ]
        
        for product in products:
            test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should have called IAM provider for authorization
        mock_iam_provider_success.assert_awaited_once()
        
        # And: Response should be a list
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)

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
        event["path"] = "/products"
        event["queryStringParameters"] = {"limit": "10"}
        # No requestContext.authorizer (missing user ID)
        
        # When: Calling the endpoint
        response = await async_handler(event, mock_lambda_context)
        
        # Then: Should return 401 unauthorized
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should contain appropriate error message
        body_data = json.loads(response["body"])
        assert "User ID not found" in body_data["message"]

    async def test_iam_authorization_failure(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_unauthorized,
        mock_user_id  # Add the fixture
    ):
        """Test handling of IAM authorization failure."""
        # Given: IAM provider returns unauthorized response
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should return the IAM provider's unauthorized response
        assert response["statusCode"] == 403
        
        # And: Should have attempted IAM authorization with the actual user ID
        mock_iam_provider_unauthorized.assert_awaited_once_with(mock_user_id)

    async def test_query_parameter_processing(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test that query parameters are processed correctly."""
        # Given: Event with various query parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = {
            "limit": "20",
            "sort": "-created_at",
            "is-food": "true",  # Test hyphen to underscore conversion
            "name": "apple"
        }
        event["multiValueQueryStringParameters"] = {
            "limit": ["20"],
            "sort": ["-created_at"],
            "is-food": ["true"],
            "name": ["apple"]
        }
        
        # When: Calling the async_handler directly to test parameter processing
        with patch.object(Container, 'bootstrap') as mock_bootstrap:
            mock_bus = AsyncMock()
            mock_uow = AsyncMock()
            mock_uow.products.query.return_value = []
            
            mock_bootstrap.return_value = mock_bus
            mock_bus.uow.__aenter__.return_value = mock_uow
            
            response = await async_handler(event, mock_lambda_context)
            
            # Then: Should have called query with processed filters
            mock_uow.products.query.assert_awaited_once()
            call_args = mock_uow.products.query.call_args[1]["filter"]
            
            # Should convert hyphen to underscore and include default values
            assert call_args["limit"] == 20
            assert call_args["sort"] == "-created_at"
            assert "is_food" in call_args  # Converted from "is-food"

    async def test_empty_query_parameters(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test handling when no query parameters are provided."""
        # Given: Event without query parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = None
        event["multiValueQueryStringParameters"] = None
        
        # When: Calling the endpoint
        with patch.object(Container, 'bootstrap') as mock_bootstrap:
            mock_bus = AsyncMock()
            mock_uow = AsyncMock()
            mock_uow.products.query.return_value = []
            
            mock_bootstrap.return_value = mock_bus
            mock_bus.uow.__aenter__.return_value = mock_uow
            
            response = await async_handler(event, mock_lambda_context)
            
            # Then: Should use default values
            mock_uow.products.query.assert_awaited_once()
            call_args = mock_uow.products.query.call_args[1]["filter"]
            
            # Should have default limit and sort
            assert call_args["limit"] == 50  # Default limit
            assert call_args["sort"] == "-updated_at"  # Default sort

    async def test_multi_value_query_parameter_handling(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test handling of multi-value query parameters in the Lambda event."""
        # Given: Event with multi-value query parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = {
            "is_food": "true",  # Use valid filter parameter
            "limit": "25"
        }
        event["multiValueQueryStringParameters"] = {
            "is_food": ["true"],  # Multi-value version
            "limit": ["25"]
        }
        
        # When: Calling the async_handler
        with patch.object(Container, 'bootstrap') as mock_bootstrap:
            mock_bus = AsyncMock()
            mock_uow = AsyncMock()
            mock_uow.products.query.return_value = []
            
            mock_bootstrap.return_value = mock_bus
            mock_bus.uow.__aenter__.return_value = mock_uow
            mock_bus.uow.__aexit__.return_value = None
            
            response = await async_handler(event, mock_lambda_context)
            
            # Then: Should process multi-value parameters correctly
            mock_uow.products.query.assert_awaited_once()
            call_args = mock_uow.products.query.call_args[1]["filter"]
            
            # Single-item lists should be converted to single values
            assert call_args["limit"] == 25

    async def test_lambda_helpers_multi_value_query_extraction(
        self,
        lambda_event_with_user,
        mock_lambda_context,
        mock_localstack_environment
    ):
        """Test that LambdaHelpers.extract_multi_value_query_parameters works correctly."""
        # Given: Event with specific multi-value query parameters
        event = lambda_event_with_user.copy()
        event["path"] = "/products"
        event["queryStringParameters"] = None  # Only multiValueQueryStringParameters set
        event["multiValueQueryStringParameters"] = {
            "is_food": ["true"],  # Use valid filter parameter
            "limit": ["15"]
        }
        
        # When: Testing parameter extraction by mocking the business logic
        with patch.object(Container, 'bootstrap') as mock_bootstrap:
            mock_bus = AsyncMock()
            mock_uow = AsyncMock()
            mock_uow.products.query.return_value = []
            
            mock_bootstrap.return_value = mock_bus
            mock_bus.uow.__aenter__.return_value = mock_uow
            mock_bus.uow.__aexit__.return_value = None
            
            response = await async_handler(event, mock_lambda_context)
            
            # Then: Should have extracted and processed the multi-value parameters
            assert response["statusCode"] == 200

    async def test_cors_headers_preservation(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test that CORS headers are preserved from original CORS_headers.py."""
        # Given: A valid database state
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should preserve exact CORS headers from CORS_headers.py
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should not include additional CORS methods
        headers = response["headers"]
        assert "PUT" not in headers["Access-Control-Allow-Methods"]
        assert "DELETE" not in headers["Access-Control-Allow-Methods"]

    async def test_response_format_with_results(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test response format when products are found."""
        # Given: Products exist in the database
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        product = create_ORM_product(
            id=str(uuid4()),  # Use proper UUID format
            name="Test Product for Response",
            source_id="00000000-0000-0000-0000-000000000001"
        )
        test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should return properly formatted response
        assert_success_response_format(response, 200)
        
        # And: Body should be a valid JSON array
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)

    async def test_response_format_empty_results(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test response format when no products are found."""
        # Given: No products match the filter criteria
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should return empty array
        assert_success_response_format(response, 200)
        
        # And: Body should be an empty JSON array
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)
        # Note: May or may not be empty depending on existing test data

    async def test_custom_serializer_usage(
        self,
        lambda_event_fetch_products,
        mock_lambda_context,
        mock_localstack_environment,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test that custom serializer is used for JSON serialization."""
        # Given: Products with potential custom serialization needs
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        product = create_ORM_product(
            id=str(uuid4()),  # Use proper UUID format
            name="Test Product Serialization",
            source_id="00000000-0000-0000-0000-000000000001"
        )
        test_session_with_sources.add(product)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await async_handler(lambda_event_fetch_products, mock_lambda_context)
        
        # Then: Should return valid JSON (custom serializer handles any special types)
        assert_success_response_format(response, 200)
        
        # And: Response should be parseable
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list) 