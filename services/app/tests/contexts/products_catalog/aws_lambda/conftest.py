"""
Fixtures for products_catalog AWS Lambda endpoint tests.

This conftest.py provides fixtures specific to testing Lambda endpoints:
- Mock Lambda events for different scenarios
- CORS header validation utilities
- Environment mocking for localstack/production testing
- Integration with existing products_catalog test infrastructure
- Test data setup for performance tests
"""

import pytest
import os
from unittest.mock import patch
from typing import Dict, Any
from uuid import uuid4

# Import domain objects for proper mock responses
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.contexts.products_catalog.core.domain.value_objects.role import Role

# Import for creating test data
from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product

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
    """Create a proper SeedUser domain object for testing."""
    # Create a basic user role for testing
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
def expected_cors_headers():
    """Expected CORS headers for all responses - matching actual endpoint CORS_headers.py."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
    }


@pytest.fixture
def mock_iam_provider_success(test_user_domain_object):
    """Mock IAMProvider.get() to return success response with proper SeedUser object."""
    with patch("src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get") as mock:
        # Use AsyncMock since IAMProvider.get() is async
        mock.return_value = {"statusCode": 200, "body": test_user_domain_object}
        yield mock


@pytest.fixture
def mock_iam_provider_unauthorized():
    """Mock IAM provider to return unauthorized response."""
    with patch("src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get") as mock:
        # Use AsyncMock since IAMProvider.get() is async
        mock.return_value = {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": '{"message": "Forbidden"}'
        }
        yield mock

@pytest.fixture
def mock_iam_provider_failure():
    """Mock IAM provider to return failure response."""
    with patch("src.contexts.products_catalog.core.adapters.internal_providers.iam.api.IAMProvider.get") as mock:
        # Use AsyncMock since IAMProvider.get() is async
        mock.return_value = {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": '{"message": "Authorization failed"}'
        }
        yield mock


@pytest.fixture
def mock_localstack_environment():
    """Mock localstack environment variables."""
    with patch.dict(os.environ, {
        "IS_LOCALSTACK": "true"  # This is what LambdaHelpers.is_localstack_environment() actually checks
    }):
        yield


@pytest.fixture
def mock_production_environment():
    """Mock production environment variables."""
    with patch.dict(os.environ, {
        "IS_LOCALSTACK": "false"  # This is what LambdaHelpers.is_localstack_environment() actually checks
    }):
        yield

@pytest.fixture
def mock_successful_auth_response():
    """Mock successful IAM authentication response."""
    user = User(
        id="test-user-123",
        roles=frozenset([Role(name="test_user", permissions=frozenset(["access_basic_features"]))])
    )
    return {
        "statusCode": 200,
        "body": user
    }

@pytest.fixture
def lambda_event_for_fetch_products():
    """Mock Lambda event for fetch_product endpoint."""
    return {
        "requestContext": {
            "authorizer": {"claims": {"sub": "test-user-123"}}
        },
        "pathParameters": None,
        "queryStringParameters": {"is_food": "true", "limit": "20"},
        "multiValueQueryStringParameters": None,
        "headers": {},
        "body": None
    }

@pytest.fixture
def lambda_event_for_get_product_by_id():
    """Mock Lambda event for get_product_by_id endpoint."""
    return {
        "requestContext": {
            "authorizer": {"claims": {"sub": "test-user-123"}}
        },
        "pathParameters": {"id": "product-123"},
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "headers": {},
        "body": None
    }

@pytest.fixture
async def performance_test_data(test_session_with_sources):
    """Create test data specifically for performance tests."""
    # Create the specific product that performance tests expect
    performance_product = create_ORM_product(
        id="product-123",
        name="Performance Test Product",
        source_id="00000000-0000-0000-0000-000000000001",  # Use existing source from create_required_sources_orm
        is_food=True
    )
    
    test_session_with_sources.add(performance_product)
    await test_session_with_sources.commit()
    
    return performance_product

def assert_cors_headers_present(response: Dict[str, Any], expected_headers: Dict[str, str]):
    """Assert that CORS headers are present in the response."""
    assert "headers" in response
    headers = response["headers"]
    
    for header_name, expected_value in expected_headers.items():
        assert header_name in headers, f"Missing CORS header: {header_name}"
        assert headers[header_name] == expected_value, f"Incorrect CORS header value for {header_name}"


def assert_error_response_format(response: Dict[str, Any], expected_status_code: int):
    """Assert error response has correct format and status code."""
    assert response["statusCode"] == expected_status_code
    assert "headers" in response
    assert "body" in response
    
    # Body should be valid JSON string
    import json
    try:
        body_data = json.loads(response["body"]) if isinstance(response["body"], str) else response["body"]
        assert "message" in body_data or isinstance(body_data, str)
    except json.JSONDecodeError:
        # Some endpoints return plain string error messages
        assert isinstance(response["body"], str)


def assert_success_response_format(response: Dict[str, Any], expected_status_code: int = 200):
    """Assert success response has correct format and status code."""
    assert response["statusCode"] == expected_status_code
    assert "headers" in response
    assert "body" in response
    
    # Body should be valid JSON
    import json
    try:
        json.loads(response["body"])
    except json.JSONDecodeError:
        pytest.fail(f"Response body is not valid JSON: {response['body']}") 