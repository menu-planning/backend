"""
Integration tests for FastAPI async authentication flow.

This module tests the async authentication behavior of FastAPI authentication
components, ensuring proper async/await patterns and no blocking I/O.
Follows behavior-focused testing principles with minimal mocking.
"""

import pytest
import asyncio
import anyio
from fastapi import Request

from src.runtimes.fastapi.auth.strategy import FastAPIAuthenticationStrategy
from src.runtimes.fastapi.auth.jwt_validator import CognitoJWTValidator, CognitoJWTClaims
from src.runtimes.fastapi.auth.user_context import UserContext
from src.contexts.shared_kernel.middleware.auth.authentication import UnifiedIAMProvider

# Use AnyIO for async testing
pytestmark = pytest.mark.anyio


class TestAsyncAuthFlow:
    """Test async authentication flow components."""
    
    @pytest.fixture
    def jwt_validator(self):
        """Create real JWT validator for testing."""
        return CognitoJWTValidator()
    
    @pytest.fixture
    def iam_provider(self):
        """Create real IAM provider for testing."""
        return UnifiedIAMProvider(
            logger_name="test_iam",
            cache_strategy="request"
        )
    
    @pytest.fixture
    def auth_strategy(self, jwt_validator, iam_provider):
        """Create authentication strategy with real dependencies."""
        return FastAPIAuthenticationStrategy(
            iam_provider=iam_provider,
            caller_context="test_context",
            jwt_validator=jwt_validator
        )
    
    @pytest.fixture
    def test_request(self):
        """Create test FastAPI request."""
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest
        
        # Create a minimal request for testing
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"authorization", b"Bearer test.token")],
            "query_string": b"",
            "client": ("127.0.0.1", 8080)
        }
        
        request = Request(scope, None)
        return request
    
    async def test_extract_user_id_from_custom_headers(self, auth_strategy, test_request):
        """Test user ID extraction from custom headers when JWT validation fails."""
        # Given: Request with custom user ID header (no valid JWT)
        test_request._headers = {"x-user-id": "test-user-123"}
        
        # When: Extract user ID from request
        user_id = await auth_strategy._extract_user_id_from_request(test_request)
        
        # Then: Should return the custom header value
        assert user_id == "test-user-123"
    
    async def test_extract_user_roles_from_custom_headers(self, auth_strategy, test_request):
        """Test user roles extraction from custom headers when JWT validation fails."""
        # Given: Request with custom roles header (no valid JWT)
        test_request._headers = {"x-user-roles": "admin,user,manager"}
        
        # When: Extract user roles from request
        roles = await auth_strategy._extract_user_roles_from_request(test_request)
        
        # Then: Should return the roles from custom header
        assert roles == ["admin", "user", "manager"]
    
    async def test_extract_auth_context_with_custom_headers(self, auth_strategy, test_request):
        """Test complete authentication context extraction using custom headers."""
        # Given: Request with custom auth headers
        test_request._headers = {
            "x-user-id": "test-user-456",
            "x-user-roles": "user,editor"
        }
        
        # When: Extract authentication context
        auth_context = await auth_strategy.extract_auth_context(test_request)
        
        # Then: Should create valid auth context from headers
        assert auth_context.user_id == "test-user-456"
        assert auth_context.user_roles == ["user", "editor"]
        assert auth_context.is_authenticated is True
        assert auth_context.caller_context == "test_context"
        assert "request_url" in auth_context.metadata
        assert auth_context.metadata["request_method"] == "GET"
    
    async def test_concurrent_auth_requests_with_custom_headers(self, auth_strategy):
        """Test that multiple concurrent auth requests work correctly."""
        # Given: Multiple requests with different custom headers
        def create_request(user_id: str, roles: str):
            from fastapi import Request
            scope = {
                "type": "http",
                "method": "GET",
                "path": f"/api/{user_id}",
                "headers": [
                    (b"x-user-id", user_id.encode()),
                    (b"x-user-roles", roles.encode())
                ],
                "query_string": b"",
                "client": ("127.0.0.1", 8080)
            }
            return Request(scope, None)
        
        requests = [
            create_request(f"user{i}", f"role{i},user")
            for i in range(5)
        ]
        
        # When: Execute concurrent authentication requests
        async def auth_request(request):
            return await auth_strategy.extract_auth_context(request)
        
        tasks = [auth_request(request) for request in requests]
        results = await asyncio.gather(*tasks)
        
        # Then: All requests should complete successfully
        assert len(results) == 5
        for i, auth_context in enumerate(results):
            assert auth_context.user_id == f"user{i}"
            assert auth_context.user_roles == [f"role{i}", "user"]
            assert auth_context.is_authenticated is True
            assert auth_context.caller_context == "test_context"
    
    async def test_no_auth_headers_returns_none(self, auth_strategy, test_request):
        """Test that requests without auth headers return None for user ID and empty roles."""
        # Given: Request with no authentication headers
        test_request._headers = {}
        
        # When: Extract user ID and roles
        user_id = await auth_strategy._extract_user_id_from_request(test_request)
        roles = await auth_strategy._extract_user_roles_from_request(test_request)
        
        # Then: Should return None/empty for missing auth
        assert user_id is None
        assert roles == []
    
    async def test_invalid_auth_context_is_not_authenticated(self, auth_strategy, test_request):
        """Test that requests without valid auth create unauthenticated context."""
        # Given: Request with no authentication headers
        test_request._headers = {}
        
        # When: Extract authentication context
        auth_context = await auth_strategy.extract_auth_context(test_request)
        
        # Then: Should create unauthenticated context
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False
        assert auth_context.caller_context == "test_context"
        assert auth_context.user_object is None
