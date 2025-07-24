"""
Fixtures for products_catalog AWS Lambda endpoint tests.

This conftest.py provides fixtures for testing the thin Lambda HTTP adapter layer:
- Mock Lambda events for different scenarios
- CORS header validation utilities  
- Environment mocking for localstack/production testing
- IAM provider mocking for authentication flow testing
- Focus on testing LambdaHelpers integration and HTTP adapter behavior only
"""

import pytest
import os
from unittest.mock import patch, AsyncMock
from typing import Dict, Any
from uuid import uuid4
import json

# Import domain objects for IAM provider mocking
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.contexts.products_catalog.core.domain.value_objects.role import Role

# Mark all tests in this module as async tests
pytestmark = [pytest.mark.anyio]


@pytest.fixture
def mock_lambda_context():
    """Mock Lambda context object."""
    class MockContext:
        function_name = "test-function"
        function_version = "1"
        invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
        memory_limit_in_mb = "128"
        remaining_time_in_millis = lambda: 30000
        log_group_name = "/aws/lambda/test-function"
        log_stream_name = "2024/01/15/[$LATEST]abcdef123456"
        aws_request_id = "12345678-1234-1234-1234-123456789012"
    
    return MockContext()


@pytest.fixture
def mock_user_id():
    """Standard test user ID in proper UUID hex format."""
    return uuid4().hex


@pytest.fixture
def mock_product_id():
    """Standard test product ID in proper UUID hex format."""
    return uuid4().hex


@pytest.fixture
def mock_source_id():
    """Standard test source ID in proper UUID hex format."""
    return uuid4().hex


@pytest.fixture
def test_user_domain_object(mock_user_id):
    """Create a proper User domain object for IAM provider mocking."""
    basic_role = Role.user()
    return User(
        id=mock_user_id,
        roles=frozenset([basic_role])
    )


@pytest.fixture  
def base_lambda_event():
    """Base Lambda event structure."""
    return {
        "requestContext": {
            "requestId": "test-request-id",
            "accountId": "123456789012",
            "resourceId": "abc123",
            "stage": "test",
            "requestTime": "25/Dec/2024:12:00:00 +0000",
            "requestTimeEpoch": 1735128000,
            "identity": {
                "sourceIp": "127.0.0.1",
                "userAgent": "test-agent"
            },
            "httpMethod": "GET",
            "resourcePath": "/test",
            "path": "/test",
            "accountId": "123456789012",
            "apiId": "test-api-id",
            "protocol": "HTTP/1.1",
            "stage": "test",
            "requestId": "test-request-id"
        },
        "headers": {
            "Host": "test-api.amazonaws.com",
            "User-Agent": "test-agent",
            "Accept": "application/json"
        },
        "isBase64Encoded": False,
        "httpMethod": "GET",
        "path": "/test",
        "pathParameters": None,
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "body": None
    }


@pytest.fixture
def lambda_event_with_user(base_lambda_event, mock_user_id):
    """Lambda event with user context for authenticated requests."""
    event = base_lambda_event.copy()
    event["requestContext"]["authorizer"] = {
        "claims": {
            "sub": mock_user_id
        },
        "userId": mock_user_id,
        "principalId": mock_user_id
    }
    return event


@pytest.fixture  
def lambda_event_get_product_by_id(lambda_event_with_user, mock_product_id):
    """Lambda event for get_product_by_id endpoint."""
    event = lambda_event_with_user.copy()
    event["pathParameters"] = {"id": mock_product_id}
    event["path"] = f"/products/{mock_product_id}"
    event["resource"] = "/products/{id}"
    return event


@pytest.fixture
def lambda_event_get_source_name_by_id(lambda_event_with_user, mock_source_id):
    """Lambda event for get_product_source_name_by_id endpoint."""
    event = lambda_event_with_user.copy()
    event["pathParameters"] = {"id": mock_source_id}
    event["path"] = f"/products/{mock_source_id}/source-name"
    event["resource"] = "/products/{id}/source-name"
    return event


@pytest.fixture
def lambda_event_fetch_products(lambda_event_with_user):
    """Lambda event for fetch_product endpoint with query parameters."""
    event = lambda_event_with_user.copy()
    event["path"] = "/products"
    event["resource"] = "/products"
    event["queryStringParameters"] = {
        "limit": "10",
        "is_food": "true"
    }
    event["multiValueQueryStringParameters"] = {
        "limit": ["10"],
        "is_food": ["true"]
    }
    return event


@pytest.fixture
def lambda_event_search_similar(lambda_event_with_user):
    """Lambda event for search_product_similar_name endpoint."""
    event = lambda_event_with_user.copy()
    event["pathParameters"] = {"name": "apple"}
    event["path"] = "/products/search/apple"
    event["resource"] = "/products/search/{name}"
    return event


@pytest.fixture
def lambda_event_fetch_source_name(lambda_event_with_user):
    """Lambda event for fetch_product_source_name endpoint."""
    event = lambda_event_with_user.copy()
    event["path"] = "/sources"
    event["resource"] = "/sources"
    return event


@pytest.fixture
def lambda_event_create_product(lambda_event_with_user):
    """Lambda event for create_product endpoint with POST body."""
    event = lambda_event_with_user.copy()
    event["httpMethod"] = "POST"
    event["path"] = "/products"
    event["resource"] = "/products"
    event["body"] = '{"name": "Test Product", "is_food": true}'
    return event


# Environment Mocking Fixtures
@pytest.fixture
def mock_localstack_environment():
    """Mock localstack environment (no authentication required)."""
    with patch.dict(os.environ, {"IS_LOCALSTACK": "true"}):
        yield


@pytest.fixture
def mock_production_environment():
    """Mock production environment (authentication required)."""
    with patch.dict(os.environ, {"IS_LOCALSTACK": "false"}):
        yield


# IAM Provider Mocking for Authentication Testing
@pytest.fixture
def mock_iam_provider_success(test_user_domain_object):
    """Mock successful IAMProvider response."""
    with patch('src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get') as mock_get:
        mock_get.return_value = {
            "statusCode": 200,
            "body": test_user_domain_object
        }
        yield mock_get


@pytest.fixture
def mock_iam_provider_unauthorized():
    """Mock unauthorized IAMProvider response."""
    with patch('src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get') as mock_get:
        mock_get.return_value = {
            "statusCode": 401,
            "body": {"message": "Unauthorized"}
        }
        yield mock_get


@pytest.fixture
def mock_iam_provider_forbidden():
    """Mock forbidden IAMProvider response."""
    with patch('src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get') as mock_get:
        mock_get.return_value = {
            "statusCode": 403,
            "body": {"message": "Forbidden"}
        }
        yield mock_get


# Business Logic Mocking - Simple immediate returns
@pytest.fixture
def mock_business_logic():
    """Mock all business logic to return immediately - we only test the HTTP adapter layer."""
    
    # Mock the API serialization layer to avoid complex domain object handling
    with patch('src.contexts.products_catalog.aws_lambda.fetch_product.ProductListTypeAdapter') as mock_list_adapter, \
         patch('src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product.ApiProduct') as mock_api_product, \
         patch('src.contexts.products_catalog.aws_lambda.fetch_product.container') as mock_fetch_container, \
         patch('src.contexts.products_catalog.aws_lambda.get_product_by_id.container') as mock_get_container:
        
        # Mock API serialization to return simple JSON
        mock_list_adapter.dump_json.return_value = b'[]'  # Empty list as bytes
        mock_api_product.from_domain.return_value = mock_api_product
        mock_api_product.model_dump_json.return_value = b'{"id": "test", "name": "test"}'
        
        # Mock business logic containers
        for container_mock in [mock_fetch_container, mock_get_container]:
            mock_bus = AsyncMock()
            mock_uow = AsyncMock()
            
            # Set up the UnitOfWork context manager
            mock_bus.uow.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_bus.uow.__aexit__ = AsyncMock(return_value=None)
            
            # Mock repository methods (won't matter since we mock serialization)
            mock_uow.products.query = AsyncMock(return_value=[])
            mock_uow.products.get = AsyncMock(return_value=object())  # Any object
            mock_uow.sources.query = AsyncMock(return_value=[])
            mock_uow.sources.get = AsyncMock(return_value=object())
            
            container_mock.bootstrap.return_value = mock_bus
        
        yield {
            'list_adapter': mock_list_adapter,
            'api_product': mock_api_product,
            'containers': {
                'fetch_product': mock_fetch_container,
                'get_product_by_id': mock_get_container
            }
        }


# CORS Headers Fixture
@pytest.fixture
def expected_cors_headers():
    """Expected CORS headers for response validation."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    }


# Response Validation Utilities
def assert_cors_headers_present(response: dict, expected_headers: dict):
    """Assert that CORS headers are present in the response."""
    response_headers = response.get("headers", {})
    for key, value in expected_headers.items():
        assert key in response_headers, f"Missing CORS header: {key}"
        assert response_headers[key] == value, f"CORS header {key} mismatch"


def assert_success_response_format(response: dict, expected_status_code: int = 200):
    """Assert that the response has the expected success format."""
    assert "statusCode" in response
    assert response["statusCode"] == expected_status_code
    assert "headers" in response
    assert "body" in response


def assert_error_response_format(response: dict, expected_status_code: int):
    """Assert that the response has the expected error format."""
    assert "statusCode" in response
    assert response["statusCode"] == expected_status_code
    assert "headers" in response
    assert "body" in response
    
    # Validate error message is present
    body = response["body"]
    if isinstance(body, str):
        import json
        try:
            body_data = json.loads(body)
            assert "message" in body_data
        except json.JSONDecodeError:
            # If not JSON, just check it's a string message
            assert isinstance(body, str) and len(body) > 0


def get_business_logic_calls(mock_business_logic_fixture):
    """Helper to extract business logic calls for verification."""
    containers = mock_business_logic_fixture['containers']
    calls = {}
    
    for name, container in containers.items():
        if container.bootstrap.called:
            bus = container.bootstrap.return_value
            calls[name] = {
                'bootstrap_called': True,
                'uow_entered': bus.uow.__aenter__.called,
                'handle_called': bus.handle.called if hasattr(bus, 'handle') else False
            }
    
    return calls 