"""
Fixtures for products_catalog AWS Lambda endpoint tests.

This conftest.py provides fixtures specific to testing Lambda endpoints:
- Mock Lambda events for different scenarios
- CORS header validation utilities
- Environment mocking for localstack/production testing
- Integration with existing products_catalog test infrastructure
"""

import pytest
import os
from unittest.mock import patch
from typing import Dict, Any
from uuid import uuid4


# Import domain objects for proper mock responses
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
    """Expected CORS headers from CORS_headers.py."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",  # Match production format with spaces
        "Access-Control-Allow-Headers": "Authorization, Content-Type"  # Match production format
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
    """Mock environment to simulate localstack (skips auth)."""
    with patch.dict(os.environ, {"IS_LOCALSTACK": "true"}):
        yield


@pytest.fixture
def mock_production_environment():
    """Mock environment to simulate production (requires auth)."""
    with patch.dict(os.environ, {"IS_LOCALSTACK": "false"}):
        yield


def assert_cors_headers_present(response: Dict[str, Any], expected_headers: Dict[str, str]):
    """Assert that CORS headers are present and correct in response."""
    assert "headers" in response
    headers = response["headers"]
    
    for key, expected_value in expected_headers.items():
        assert key in headers, f"Missing CORS header: {key}"
        assert headers[key] == expected_value, f"Incorrect CORS header {key}: expected {expected_value}, got {headers[key]}"


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