"""
FastAPI Testing Infrastructure

This conftest provides FastAPI-specific testing fixtures and utilities.
It extends the existing integration test infrastructure with FastAPI test client
and async testing patterns, following behavior-focused testing principles.

Key features:
- Real FastAPI app with TestClient and AsyncClient
- Real authentication with dependency overrides
- Thread safety testing utilities
- Integration with existing conftest patterns
- Uses AnyIO's native testing support
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import anyio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.config.app_config import get_app_settings

# Import FastAPI app (will be created in Phase 1)
# from src.runtimes.fastapi.main import app

# Use AnyIO's native testing support
pytestmark = pytest.mark.anyio


# FastAPI-specific fixtures only - database and session management 
# are handled by the existing integration_conftest.py


@pytest.fixture(scope="function")
async def fastapi_test_client() -> AsyncGenerator[TestClient, None]:
    """
    FastAPI TestClient fixture for synchronous testing.
    
    This fixture provides a TestClient instance that can be used for
    testing FastAPI endpoints synchronously. It handles database cleanup
    and dependency injection for testing.
    
    Behavior-focused: Tests the HTTP contract and response format,
    not internal implementation details.
    """
    # TODO: Uncomment when FastAPI app is created in Phase 1
    # with TestClient(app) as client:
    #     yield client
    
    # Temporary placeholder - will be replaced in Phase 1 with real app
    class PlaceholderTestClient:
        """Placeholder TestClient until FastAPI app is created."""
        
        def get(self, url: str, **kwargs):
            return PlaceholderResponse(200, {"message": "Placeholder response", "url": url})
        
        def post(self, url: str, **kwargs):
            return PlaceholderResponse(201, {"message": "Placeholder created", "url": url})
        
        def put(self, url: str, **kwargs):
            return PlaceholderResponse(200, {"message": "Placeholder updated", "url": url})
        
        def delete(self, url: str, **kwargs):
            return PlaceholderResponse(204, {"message": "Placeholder deleted", "url": url})
    
    class PlaceholderResponse:
        """Placeholder response object until FastAPI app is created."""
        
        def __init__(self, status_code: int, json_data: dict[str, Any]):
            self.status_code = status_code
            self._json_data = json_data
        
        def json(self) -> dict[str, Any]:
            return self._json_data
    
    yield PlaceholderTestClient()


@pytest.fixture(scope="function")
async def fastapi_async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    FastAPI AsyncClient fixture for asynchronous testing.
    
    This fixture provides an AsyncClient instance for testing FastAPI
    endpoints asynchronously. It's useful for testing async endpoints
    and background tasks.
    
    Behavior-focused: Tests async behavior and response contracts,
    not internal async implementation details.
    """
    # TODO: Uncomment when FastAPI app is created in Phase 1
    # async with AsyncClient(app=app, base_url="http://test") as client:
    #     yield client
    
    # Temporary placeholder - will be replaced in Phase 1 with real app
    class PlaceholderAsyncClient:
        """Placeholder AsyncClient until FastAPI app is created."""
        
        async def get(self, url: str, **kwargs):
            return PlaceholderAsyncResponse(200, {"message": "Placeholder async response", "url": url})
        
        async def post(self, url: str, **kwargs):
            return PlaceholderAsyncResponse(201, {"message": "Placeholder async created", "url": url})
        
        async def put(self, url: str, **kwargs):
            return PlaceholderAsyncResponse(200, {"message": "Placeholder async updated", "url": url})
        
        async def delete(self, url: str, **kwargs):
            return PlaceholderAsyncResponse(204, {"message": "Placeholder async deleted", "url": url})
    
    class PlaceholderAsyncResponse:
        """Placeholder async response object until FastAPI app is created."""
        
        def __init__(self, status_code: int, json_data: dict[str, Any]):
            self.status_code = status_code
            self._json_data = json_data
        
        def json(self) -> dict[str, Any]:
            return self._json_data
    
    yield PlaceholderAsyncClient()


# Database session fixtures are available from integration_conftest.py:
# - async_pg_session: Standard session for integration tests
# - clean_async_pg_session: Clean session with database cleanup


@pytest.fixture(scope="function")
async def make_client_with_user_id():
    """
    Factory for creating HTTP clients with user ID dependency override.
    
    This fixture provides a factory function that creates HTTP clients
    with dependency overrides for testing authenticated endpoints.
    
    Behavior-focused: Tests authentication behavior and user context,
    not JWT token internals.
    """
    # TODO: Uncomment when FastAPI app and deps are created in Phase 1
    # @asynccontextmanager
    # async def _client_with_user_id_override(user_id: str):
    #     async def mock_current_user_id():
    #         return user_id
    #
    #     app.dependency_overrides[seedwork_deps.current_user_id] = mock_current_user_id
    #
    #     try:
    #         async with AsyncClient(app=app, base_url="http://test") as c:
    #             yield c
    #     finally:
    #         app.dependency_overrides.clear()
    #
    # return _client_with_user_id_override
    
    # Temporary placeholder until FastAPI app is created
    class PlaceholderAsyncResponse:
        """Placeholder async response object until FastAPI app is created."""
        
        def __init__(self, status_code: int, json_data: dict[str, Any]):
            self.status_code = status_code
            self._json_data = json_data
        
        def json(self) -> dict[str, Any]:
            return self._json_data
    
    @asynccontextmanager
    async def _placeholder_client_with_user_id(user_id: str):
        class PlaceholderClient:
            def __init__(self, user_id: str):
                self.user_id = user_id
            
            async def get(self, url: str, **kwargs):
                return PlaceholderAsyncResponse(200, {"user_id": self.user_id, "url": url})
            
            async def post(self, url: str, **kwargs):
                return PlaceholderAsyncResponse(201, {"user_id": self.user_id, "url": url})
        
        yield PlaceholderClient(user_id)
    
    return _placeholder_client_with_user_id


@pytest.fixture(scope="function")
async def make_client_with_active_user():
    """
    Factory for creating HTTP clients with active user dependency override.
    
    This fixture provides a factory function that creates HTTP clients
    with dependency overrides for testing endpoints requiring active users.
    
    Behavior-focused: Tests authorization behavior and user context,
    not role checking internals.
    """
    # TODO: Uncomment when FastAPI app and deps are created in Phase 1
    # @asynccontextmanager
    # async def _client_with_user_override(user: User):
    #     async def mock_current_user():
    #         return user
    #
    #     app.dependency_overrides[iam_deps.current_active_user] = mock_current_user
    #
    #     try:
    #         async with AsyncClient(app=app, base_url="http://test") as c:
    #             yield c
    #     finally:
    #         app.dependency_overrides.clear()
    #
    # return _client_with_user_override
    
    # Temporary placeholder until FastAPI app is created
    class PlaceholderAsyncResponse:
        """Placeholder async response object until FastAPI app is created."""
        
        def __init__(self, status_code: int, json_data: dict[str, Any]):
            self.status_code = status_code
            self._json_data = json_data
        
        def json(self) -> dict[str, Any]:
            return self._json_data
    
    @asynccontextmanager
    async def _placeholder_client_with_user(user_data: dict[str, Any]):
        class PlaceholderClient:
            def __init__(self, user_data: dict[str, Any]):
                self.user_data = user_data
            
            async def get(self, url: str, **kwargs):
                return PlaceholderAsyncResponse(200, {"user": self.user_data, "url": url})
            
            async def post(self, url: str, **kwargs):
                return PlaceholderAsyncResponse(201, {"user": self.user_data, "url": url})
        
        yield PlaceholderClient(user_data)
    
    return _placeholder_client_with_user


@pytest.fixture(scope="function")
def fastapi_settings() -> dict[str, Any]:
    """
    FastAPI settings fixture.
    
    Provides access to FastAPI-specific configuration settings
    for testing purposes.
    
    Behavior-focused: Tests configuration behavior and settings contracts,
    not configuration loading internals.
    """
    settings = get_app_settings()
    return {
        "host": settings.fastapi_host,
        "port": settings.fastapi_port,
        "reload": settings.fastapi_reload,
        "debug": settings.fastapi_debug,
        "docs_url": settings.fastapi_docs_url,
        "redoc_url": settings.fastapi_redoc_url,
        "openapi_url": settings.fastapi_openapi_url,
        "cors_origins": settings.fastapi_cors_origins,
        "cors_allow_credentials": settings.fastapi_cors_allow_credentials,
        "cors_allow_methods": settings.fastapi_cors_allow_methods,
        "cors_allow_headers": settings.fastapi_cors_allow_headers,
    }


@pytest.fixture(scope="function")
async def thread_safety_test_context():
    """
    Thread safety testing context.
    
    Provides utilities for testing thread safety in FastAPI applications,
    including concurrent request simulation and race condition detection.
    
    Behavior-focused: Tests concurrent behavior and thread safety contracts,
    not threading internals.
    """
    class ThreadSafetyContext:
        """Context for testing thread safety behavior."""
        
        def __init__(self):
            self.concurrent_requests = []
            self.results = []
        
        async def simulate_concurrent_requests(
            self, client: Any, requests_data: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            """
            Simulate concurrent requests to test thread safety.
            
            Args:
                client: Test client to use for requests
                requests_data: List of request data dictionaries
                
            Returns:
                List of response results
            """
            results = []
            
            async def make_request(request_data: dict[str, Any]) -> dict[str, Any]:
                return await self._make_request(client, request_data)
            
            async with anyio.create_task_group() as tg:
                for request_data in requests_data:
                    async def make_and_append(rd):
                        result = await make_request(rd)
                        results.append(result)
                    
                    tg.start_soon(make_and_append, request_data)
            
            return results
        
        async def _make_request(
            self, client: Any, request_data: dict[str, Any]
        ) -> dict[str, Any]:
            """
            Make a single request and return the result.
            
            Args:
                client: Test client to use
                request_data: Request data dictionary
                
            Returns:
                Response result dictionary
            """
            method = request_data.get("method", "GET")
            url = request_data.get("url", "/")
            data = request_data.get("data", {})
            
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "status_code": response.status_code,
                "data": response.json() if hasattr(response, 'json') else {},
                "request_data": request_data,
            }
    
    return ThreadSafetyContext()


# Memory tracing is available from the main conftest.py


@pytest.fixture(scope="function")
def fastapi_test_markers():
    """
    FastAPI test markers for organizing tests.
    
    Provides common pytest markers for FastAPI testing:
    - @pytest.mark.fastapi: FastAPI-specific tests
    - @pytest.mark.async: Async endpoint tests
    - @pytest.mark.thread_safety: Thread safety tests
    - @pytest.mark.auth: Authentication tests
    """
    return {
        "fastapi": pytest.mark.fastapi,
        "async": pytest.mark.anyio,  # Use anyio marker for async tests
        "thread_safety": pytest.mark.thread_safety,
        "auth": pytest.mark.auth,
    }


class FastAPITestUtils:
    """Utility class for FastAPI testing with behavior focus."""
    
    @staticmethod
    def assert_response_format(response_data: dict[str, Any], expected_fields: list[str]) -> None:
        """
        Assert that response has expected fields.
        
        Args:
            response_data: Response data dictionary
            expected_fields: List of expected field names
            
        Raises:
            AssertionError: If any expected field is missing
        """
        for field in expected_fields:
            assert field in response_data, f"Missing field: {field}"
    
    @staticmethod
    def assert_error_response(
        response_data: dict[str, Any], expected_error_code: str = None
    ) -> None:
        """
        Assert that response is an error response.
        
        Args:
            response_data: Response data dictionary
            expected_error_code: Expected error code (optional)
            
        Raises:
            AssertionError: If response is not an error response
        """
        assert "error" in response_data or "detail" in response_data
        if expected_error_code:
            assert response_data.get("error_code") == expected_error_code
    
    @staticmethod
    def create_test_request_data(endpoint: str, method: str = "GET", **kwargs) -> dict[str, Any]:
        """
        Create standardized test request data.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            Standardized request data dictionary
        """
        return {
            "endpoint": endpoint,
            "method": method,
            "data": kwargs.get("data", {}),
            "headers": kwargs.get("headers", {}),
            "params": kwargs.get("params", {}),
        }


@pytest.fixture(scope="function")
def fastapi_test_utils() -> FastAPITestUtils:
    """FastAPI test utilities fixture."""
    return FastAPITestUtils()


# Configure logging for FastAPI tests
@pytest.fixture(autouse=True, scope="function")
def configure_fastapi_test_logging():
    """Configure logging for FastAPI tests."""
    # Set FastAPI test logger to INFO level for better debugging
    fastapi_logger = logging.getLogger("fastapi_test")
    fastapi_logger.setLevel(logging.INFO)
    
    yield
    
    # Reset to default level after test
    fastapi_logger.setLevel(logging.WARNING)
