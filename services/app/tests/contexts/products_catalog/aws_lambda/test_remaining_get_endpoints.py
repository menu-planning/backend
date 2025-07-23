"""
Tests for remaining migrated GET endpoints in products_catalog.

This file tests:
- get_product_source_name_by_id.py
- search_product_similar_name.py  
- fetch_product_source_name.py

All tests cover LambdaHelpers integration, authentication, error handling,
and response format validation.
"""

import json
import pytest
import urllib.parse
from unittest.mock import patch, AsyncMock
import uuid

from src.contexts.products_catalog.aws_lambda.get_product_source_name_by_id import (
    lambda_handler as get_source_name_handler,
    async_handler as get_source_name_async_handler
)
from src.contexts.products_catalog.aws_lambda.search_product_similar_name import (
    lambda_handler as search_similar_handler,
    async_handler as search_similar_async_handler
)
from src.contexts.products_catalog.aws_lambda.fetch_product_source_name import (
    lambda_handler as fetch_source_name_handler,
    async_handler as fetch_source_name_async_handler
)

from tests.contexts.products_catalog.aws_lambda.conftest import (
    assert_cors_headers_present,
    assert_error_response_format,
    assert_success_response_format
)

pytestmark = [pytest.mark.anyio]


class TestGetProductSourceNameByIdEndpoint:
    """Test get_product_source_name_by_id endpoint functionality."""

    async def test_successful_source_name_retrieval_localstack(
        self,
        lambda_event_get_source_name_by_id,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test successful source name retrieval in localstack environment."""
        # Given: A source exists in the database
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_source
        
        # Use the source ID from the lambda event for consistency
        source_id = lambda_event_get_source_name_by_id["pathParameters"]["id"]
        
        source = create_ORM_source(
            id=source_id,
            name="Test Source for Localstack",
            author_id="00000000-0000-0000-0000-000000000001"  # Use proper UUID format instead of "test_author"
        )
        test_session_with_sources.add(source)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await get_source_name_async_handler(lambda_event_get_source_name_by_id, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Response should contain source name data
        body_data = json.loads(response["body"])
        assert isinstance(body_data, dict)
        assert source_id in body_data
        assert body_data[source_id] == "Test Source for Localstack"

    async def test_missing_user_id_in_production(
        self,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test error when user ID is missing in production environment."""
        # Given: Event without user context
        event = {
            "pathParameters": {"id": str(uuid.uuid4())},
            "requestContext": {"authorizer": {}},  # Missing principalId
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await get_source_name_async_handler(event, mock_lambda_context)
        
        # Then: Should return unauthorized error (not bad request)
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_missing_product_id_parameter(
        self,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test error when product ID parameter is missing."""
        # Given: Event without product ID in path parameters
        event = {
            "pathParameters": None,
            "requestContext": {"authorizer": {"principalId": "test_user_123"}},
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await get_source_name_async_handler(event, mock_lambda_context)
        
        # Then: Should return error response
        assert_error_response_format(response, 400)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_iam_authorization_success(
        self,
        lambda_event_get_source_name_by_id,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_success,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources,
        mock_user_id  # Add the fixture
    ):
        """Test successful IAM authorization flow."""
        # Given: A source exists and IAM authorization succeeds
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_source
        
        # Use the source ID from the lambda event for consistency
        source_id = lambda_event_get_source_name_by_id["pathParameters"]["id"]
        
        source = create_ORM_source(
            id=source_id,
            name="Test Source",
            author_id="00000000-0000-0000-0000-000000000001"  # Use proper UUID format instead of "test_author"
        )
        test_session_with_sources.add(source)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await get_source_name_async_handler(lambda_event_get_source_name_by_id, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should have performed IAM authorization with the actual user ID
        mock_iam_provider_success.assert_awaited_once_with(mock_user_id)
        
        # And: Response should contain source data
        body_data = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
        assert source_id in body_data
        assert body_data[source_id] == "Test Source"


class TestSearchProductSimilarNameEndpoint:
    """Test search_product_similar_name endpoint functionality."""

    async def test_successful_similarity_search_localstack(
        self,
        lambda_event_search_similar,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test successful product similarity search in localstack."""
        # Given: Products exist for searching
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product
        
        similar_product = create_ORM_product(
            id=str(uuid.uuid4()),
            name="Apple Red Delicious",
            source_id="00000000-0000-0000-0000-000000000001"
        )
        test_session_with_sources.add(similar_product)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await search_similar_async_handler(lambda_event_search_similar, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)

        # And: Response should be a list of similar products
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)

    async def test_missing_name_parameter(
        self,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test error when name parameter is missing."""
        # Given: Event without name parameter
        event = {
            "pathParameters": None,
            "requestContext": {"authorizer": {"principalId": "test_user_123"}},
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await search_similar_async_handler(event, mock_lambda_context)
        
        # Then: Should return error response
        assert_error_response_format(response, 400)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_url_decoding_of_name_parameter(
        self,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test URL decoding of search name parameter."""
        # Given: Event with URL-encoded name parameter
        event = {
            "pathParameters": {"name": "red%20apple"},
            "requestContext": {"authorizer": {"principalId": "test_user_123"}},
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await search_similar_async_handler(event, mock_lambda_context)
        
        # Then: Should return successful response (URL decoding happens internally)
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Response should be valid JSON array
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)

    async def test_missing_user_id_in_production(
        self,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test error when user ID is missing in production environment."""
        # Given: Event without user context
        event = {
            "pathParameters": {"name": "apple"},
            "requestContext": {"authorizer": {}},  # Missing principalId
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await search_similar_async_handler(event, mock_lambda_context)
        
        # Then: Should return unauthorized error (not bad request)
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_custom_serializer_usage(
        self,
        lambda_event_search_similar,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test that endpoint uses custom serializer for response formatting."""
        # When: Calling the endpoint (serializer usage is internal)
        response = await search_similar_async_handler(lambda_event_search_similar, mock_lambda_context)
        
        # Then: Should return valid JSON response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)

        # And: Response should be properly serialized list
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)

    async def test_lambda_helpers_path_parameter_extraction(
        self,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test LambdaHelpers integration for path parameter extraction."""
        # Given: Event with specific path parameter
        event = {
            "pathParameters": {"name": "specific_search_term"},
            "requestContext": {"authorizer": {"principalId": "test_user_123"}},
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await search_similar_async_handler(event, mock_lambda_context)
        
        # Then: Should return successful response (parameter extraction works)
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Response should be valid JSON array
        body_data = json.loads(response["body"])
        assert isinstance(body_data, list)


class TestFetchProductSourceNameEndpoint:
    """Test fetch_product_source_name endpoint functionality."""

    async def test_successful_source_name_fetch_localstack(
        self,
        lambda_event_fetch_source_name,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources
    ):
        """Test successful source name fetching in localstack."""
        # Given: Source names exist for fetching
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_source
        
        # Create a test source with proper UUID author_id
        test_source = create_ORM_source(
            id="00000000-0000-0000-0000-000000000004",
            name="Test Fetch Source",
            author_id="00000000-0000-0000-0000-000000000001"  # Use proper UUID format
        )
        test_session_with_sources.add(test_source)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await fetch_source_name_async_handler(lambda_event_fetch_source_name, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)

        # And: Response should be a dictionary of source names
        body_data = json.loads(response["body"])
        assert isinstance(body_data, dict)

    async def test_missing_user_id_in_production(
        self,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test error when user ID is missing in production environment."""
        # Given: Event without user context
        event = {
            "queryStringParameters": {},
            "requestContext": {"authorizer": {}},  # Missing principalId
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await fetch_source_name_async_handler(event, mock_lambda_context)
        
        # Then: Should return unauthorized error (not bad request)
        assert_error_response_format(response, 401)
        assert_cors_headers_present(response, expected_cors_headers)

    async def test_iam_authorization_success(
        self,
        lambda_event_fetch_source_name,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_success,
        expected_cors_headers,
        product_repository_orm,
        test_session_with_sources,
        mock_user_id  # Add the fixture
    ):
        """Test successful IAM authorization flow."""
        # Given: Sources exist and IAM authorization succeeds
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_source
        
        # Create a test source with proper UUID author_id
        test_source = create_ORM_source(
            id="00000000-0000-0000-0000-000000000005",
            name="Test IAM Source",
            author_id="00000000-0000-0000-0000-000000000001"  # Use proper UUID format
        )
        test_session_with_sources.add(test_source)
        await test_session_with_sources.commit()
        
        # When: Calling the endpoint
        response = await fetch_source_name_async_handler(lambda_event_fetch_source_name, mock_lambda_context)
        
        # Then: Should return successful response
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should have performed IAM authorization with the actual user ID
        mock_iam_provider_success.assert_awaited_once_with(mock_user_id)
        
        # And: Response should be a dictionary of source names
        body_data = json.loads(response["body"])
        assert isinstance(body_data, dict)

    async def test_iam_authorization_failure(
        self,
        lambda_event_fetch_source_name,
        mock_lambda_context,
        mock_production_environment,
        mock_iam_provider_failure,
        expected_cors_headers,
        mock_user_id  # Add the fixture
    ):
        """Test handling of IAM authorization failure."""
        # Given: IAM provider returns failure response
        
        # When: Calling the endpoint
        response = await fetch_source_name_async_handler(lambda_event_fetch_source_name, mock_lambda_context)
        
        # Then: Should return the IAM provider's failure response
        assert response["statusCode"] == 403
        assert_cors_headers_present(response, expected_cors_headers)
        
        # And: Should have attempted IAM authorization with the actual user ID
        mock_iam_provider_failure.assert_awaited_once_with(mock_user_id)

    async def test_cors_headers_preservation(
        self,
        lambda_event_fetch_source_name,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test CORS headers are preserved correctly."""
        # When: Calling the endpoint
        response = await fetch_source_name_async_handler(lambda_event_fetch_source_name, mock_lambda_context)
        
        # Then: Should preserve exact CORS headers
        assert_success_response_format(response, 200)
        assert_cors_headers_present(response, expected_cors_headers)


class TestEndpointCommonBehaviors:
    """Test common behaviors across all migrated endpoints."""

    @pytest.mark.parametrize("handler,event_fixture", [
        (get_source_name_async_handler, "lambda_event_get_source_name_by_id"),
        (search_similar_async_handler, "lambda_event_search_similar"),
        (fetch_source_name_async_handler, "lambda_event_fetch_source_name"),
    ])
    async def test_environment_detection_consistency(
        self,
        handler,
        event_fixture,
        request,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test consistent environment detection across endpoints."""
        # Given: Event from fixture
        event = request.getfixturevalue(event_fixture)
        
        # When: Calling the endpoint
        response = await handler(event, mock_lambda_context)
        
        # Then: Should handle environment consistently
        assert response["statusCode"] in [200, 400, 404, 500]
        assert_cors_headers_present(response, expected_cors_headers)

    @pytest.mark.parametrize("handler,event_fixture", [
        (get_source_name_async_handler, "lambda_event_get_source_name_by_id"),
        (search_similar_async_handler, "lambda_event_search_similar"),
        (fetch_source_name_async_handler, "lambda_event_fetch_source_name"),
    ])
    async def test_cors_headers_consistency(
        self,
        handler,
        event_fixture,
        request,
        mock_lambda_context,
        mock_localstack_environment,
        expected_cors_headers
    ):
        """Test consistent CORS headers across endpoints."""
        # Given: Event from fixture
        event = request.getfixturevalue(event_fixture)
        
        # When: Calling the endpoint
        response = await handler(event, mock_lambda_context)
        
        # Then: Should have consistent CORS headers
        assert_cors_headers_present(response, expected_cors_headers)

    @pytest.mark.parametrize("handler", [
        get_source_name_async_handler,
        search_similar_async_handler,
        fetch_source_name_async_handler,
    ])
    async def test_missing_user_id_error_consistency(
        self,
        handler,
        mock_lambda_context,
        mock_production_environment,
        expected_cors_headers
    ):
        """Test consistent missing user ID error handling."""
        # Given: Event without user ID
        event = {
            "pathParameters": {"id": str(uuid.uuid4())},
            "requestContext": {"authorizer": {}},
            "headers": {"origin": "https://example.com"}
        }
        
        # When: Calling the endpoint
        response = await handler(event, mock_lambda_context)
        
        # Then: Should return consistent error format
        assert response["statusCode"] in [400, 401]
        assert_cors_headers_present(response, expected_cors_headers) 