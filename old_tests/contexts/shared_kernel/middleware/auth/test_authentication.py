"""
Behavior tests for authentication middleware.

Tests focus on what the authentication middleware does (outcomes, side effects,
return values) rather than how it does it (internal method calls, private
variables, implementation details).

Following the test-behavior-focus philosophy:
- Test behavior, not implementation
- Focus on user-facing functionality and business logic
- Test outcomes and observable effects rather than internal state
- Ensure tests remain maintainable when implementation details change
"""

from typing import Any

import pytest

from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthContext,
    AuthenticationError,
    AuthenticationMiddleware,
    AuthorizationError,
    AuthPolicy,
    create_auth_middleware,
)


class TestAuthPolicyBehavior:
    """Test authentication policy configuration and behavior."""

    def test_policy_requires_authentication_by_default(self):
        """Policy should require authentication by default."""
        policy = AuthPolicy()
        assert policy.is_authenticated_required() is True

    def test_policy_can_disable_authentication_requirement(self):
        """Policy should allow disabling authentication requirement."""
        policy = AuthPolicy(require_authentication=False)
        assert policy.is_authenticated_required() is False

    def test_policy_allows_any_role_when_no_restrictions(self):
        """Policy should allow any authenticated user when no role restrictions."""
        policy = AuthPolicy()
        user_roles = ["user", "admin", "guest"]
        assert policy.has_required_role(user_roles) is True

    def test_policy_enforces_role_restrictions_when_configured(self):
        """Policy should enforce role restrictions when configured."""
        policy = AuthPolicy(allowed_roles=["admin", "moderator"])

        # User has required role
        assert policy.has_required_role(["admin"]) is True
        assert policy.has_required_role(["moderator"]) is True

        # User lacks required role
        assert policy.has_required_role(["user"]) is False
        assert policy.has_required_role(["guest"]) is False

    def test_policy_handles_empty_user_roles(self):
        """Policy should handle users with no roles."""
        policy = AuthPolicy(allowed_roles=["admin"])
        assert policy.has_required_role([]) is False


class TestAuthContextBehavior:
    """Test authentication context behavior and role checking."""

    def test_context_creation_with_minimal_data(self):
        """Context should be created with minimal required data."""
        context = AuthContext()
        assert context.user_id is None
        assert context.user_roles == []
        assert context.is_authenticated is False
        assert context.metadata == {}

    def test_context_creation_with_full_data(self):
        """Context should be created with all provided data."""
        metadata = {"source": "jwt", "exp": 1234567890}
        context = AuthContext(
            user_id="user123",
            user_roles=["admin", "moderator"],
            is_authenticated=True,
            metadata=metadata,
        )

        assert context.user_id == "user123"
        assert context.user_roles == ["admin", "moderator"]
        assert context.is_authenticated is True
        assert context.metadata == metadata

    def test_context_role_checking(self):
        """Context should correctly check user roles."""
        context = AuthContext(
            user_id="user123",
            user_roles=["admin", "moderator"],
            is_authenticated=True,
        )

        assert context.has_role("admin") is True
        assert context.has_role("moderator") is True
        assert context.has_role("user") is False
        assert context.has_role("") is False

    def test_context_any_role_checking(self):
        """Context should check if user has any of specified roles."""
        context = AuthContext(
            user_id="user123",
            user_roles=["admin", "moderator"],
            is_authenticated=True,
        )

        assert context.has_any_role(["admin"]) is True
        assert context.has_any_role(["moderator", "user"]) is True
        assert context.has_any_role(["user", "guest"]) is False
        assert context.has_any_role([]) is False

    def test_context_string_representation(self):
        """Context should have meaningful string representation."""
        context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=True,
        )

        repr_str = repr(context)
        assert "user123" in repr_str
        assert "admin" in repr_str
        assert "True" in repr_str


class TestAuthenticationMiddlewareBehavior:
    """Test authentication middleware behavior and composition."""

    @pytest.fixture
    def mock_handler(self):
        """Create a mock handler for testing."""

        async def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
            return {"statusCode": 200, "body": "success", "event": event}

        return handler

    @pytest.fixture
    def mock_event(self):
        """Create a mock AWS Lambda event."""
        return {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user123",
                        "cognito:groups": ["admin", "user"],
                    }
                }
            }
        }

    def test_middleware_creation_with_defaults(self):
        """Middleware should be created with sensible defaults."""
        middleware = AuthenticationMiddleware()
        assert middleware.name == "AuthenticationMiddleware"
        assert middleware.timeout is None
        assert middleware.policy is not None
        assert middleware.policy.is_authenticated_required() is True

    def test_middleware_creation_with_custom_policy(self):
        """Middleware should accept custom authentication policy."""
        policy = AuthPolicy(require_authentication=False)
        middleware = AuthenticationMiddleware(policy=policy)
        assert middleware.policy is policy
        assert middleware.policy.is_authenticated_required() is False

    def test_middleware_creation_with_custom_name_and_timeout(self):
        """Middleware should accept custom name and timeout."""
        timeout = 30.0
        middleware = AuthenticationMiddleware(name="CustomAuth", timeout=timeout)
        assert middleware.name == "CustomAuth"
        assert middleware.timeout == timeout

    @pytest.mark.anyio
    async def test_middleware_passes_through_authenticated_requests(
        self, mock_handler, mock_event
    ):
        """Middleware should pass through properly authenticated requests."""
        middleware = AuthenticationMiddleware()
        mock_context = {"function_name": "test"}
        result = await middleware(mock_handler, mock_event, mock_context)

        status_code = 200
        assert result["statusCode"] == status_code
        assert result["body"] == "success"
        assert "_auth_context" in result["event"]

        auth_context = result["event"]["_auth_context"]
        assert auth_context.user_id == "user123"
        assert "admin" in auth_context.user_roles
        assert auth_context.is_authenticated is True

    @pytest.mark.anyio
    async def test_middleware_rejects_unauthenticated_requests(self, mock_handler):
        """Middleware should reject unauthenticated requests."""
        middleware = AuthenticationMiddleware()
        event = {"requestContext": {"authorizer": {"claims": {}}}}
        mock_context = {"function_name": "test"}

        with pytest.raises(AuthenticationError):
            await middleware(mock_handler, event, mock_context)

    @pytest.mark.anyio
    async def test_middleware_enforces_role_restrictions(
        self, mock_handler, mock_event
    ):
        """Middleware should enforce role-based access control."""
        policy = AuthPolicy(allowed_roles=["super_admin"])
        middleware = AuthenticationMiddleware(policy=policy)
        mock_context = {"function_name": "test"}

        with pytest.raises(AuthorizationError):
            await middleware(mock_handler, mock_event, mock_context)

    @pytest.mark.anyio
    async def test_middleware_allows_bypassing_authentication(
        self, mock_handler, mock_event
    ):
        """Middleware should allow bypassing authentication when configured."""
        policy = AuthPolicy(require_authentication=False)
        middleware = AuthenticationMiddleware(policy=policy)
        mock_context = {"function_name": "test"}

        result = await middleware(mock_handler, mock_event, mock_context)
        assert result["statusCode"] == 200

        auth_context = result["event"]["_auth_context"]
        # When auth is not required but valid credentials exist, user should still be
        # marked as authenticated
        assert auth_context.is_authenticated is True
        assert auth_context.user_id == "user123"
        assert "admin" in auth_context.user_roles

    @pytest.mark.anyio
    async def test_middleware_bypasses_authentication_when_no_credentials(
        self, mock_handler
    ):
        """Middleware should bypass authentication when not required and no credentials."""
        policy = AuthPolicy(require_authentication=False)
        middleware = AuthenticationMiddleware(policy=policy)
        mock_context = {"function_name": "test"}

        # Event with no authentication credentials
        event = {"requestContext": {"authorizer": {"claims": {}}}}

        result = await middleware(mock_handler, event, mock_context)
        assert result["statusCode"] == 200

        auth_context = result["event"]["_auth_context"]
        # When auth is not required and no credentials, user should be marked as unauthenticated
        assert auth_context.is_authenticated is False
        assert auth_context.user_id is None
        assert auth_context.user_roles == []

    @pytest.mark.anyio
    async def test_middleware_extracts_jwt_claims_correctly(self, mock_handler):
        """Middleware should extract JWT claims from various sources."""
        middleware = AuthenticationMiddleware()
        mock_context = {"function_name": "test"}

        # Test custom roles claim
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user456",
                        "custom:roles": "admin,moderator",
                    }
                }
            }
        }

        result = await middleware(mock_handler, event, mock_context)
        auth_context = result["event"]["_auth_context"]
        assert auth_context.user_id == "user456"
        assert "admin" in auth_context.user_roles
        assert "moderator" in auth_context.user_roles

        # Test OAuth scope claim
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user789",
                        "scope": "read write admin",
                    }
                }
            }
        }

        result = await middleware(mock_handler, event, mock_context)
        auth_context = result["event"]["_auth_context"]
        assert auth_context.user_id == "user789"
        assert "read" in auth_context.user_roles
        assert "write" in auth_context.user_roles
        assert "admin" in auth_context.user_roles

    def test_middleware_get_auth_context(self):
        """Middleware should retrieve auth context from events."""
        middleware = AuthenticationMiddleware()
        event = {"_auth_context": "test_context"}

        context = middleware.get_auth_context(event)
        assert context == "test_context"

        # Should return None when no context exists
        empty_event = {}
        context = middleware.get_auth_context(empty_event)
        assert context is None


class TestCreateAuthMiddlewareFunction:
    """Test the convenience function for creating authentication middleware."""

    def test_create_middleware_with_defaults(self):
        """Function should create middleware with sensible defaults."""
        middleware = create_auth_middleware()
        assert isinstance(middleware, AuthenticationMiddleware)
        assert middleware.policy.is_authenticated_required() is True
        assert middleware.policy.allowed_roles == []

    def test_create_middleware_with_custom_configuration(self):
        """Function should create middleware with custom configuration."""
        middleware = create_auth_middleware(
            require_authentication=False,
            allowed_roles=["admin", "moderator"],
            name="CustomAuth",
            timeout=60.0,
        )

        assert middleware.name == "CustomAuth"
        assert middleware.timeout == 60.0
        assert middleware.policy.is_authenticated_required() is False
        assert middleware.policy.allowed_roles == ["admin", "moderator"]

    def test_create_middleware_with_role_restrictions(self):
        """Function should create middleware with role restrictions."""
        middleware = create_auth_middleware(allowed_roles=["admin"])
        assert middleware.policy.allowed_roles == ["admin"]
        assert middleware.policy.has_required_role(["admin"]) is True
        assert middleware.policy.has_required_role(["user"]) is False


class TestAuthenticationMiddlewareIntegration:
    """Test authentication middleware integration with real scenarios."""

    @pytest.fixture
    def handler_with_auth_check(self):
        """Create a handler that checks authentication context."""

        async def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
            auth_context = event.get("_auth_context")
            if not auth_context or not auth_context.is_authenticated:
                return {"statusCode": 401, "body": "Unauthorized"}

            user_id = auth_context.user_id
            return {
                "statusCode": 200,
                "body": f"Hello {user_id}",
                "user_roles": auth_context.user_roles,
            }

        return handler

    @pytest.mark.anyio
    async def test_middleware_integration_with_handler(self, handler_with_auth_check):
        """Middleware should integrate seamlessly with handlers."""
        middleware = AuthenticationMiddleware()
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "testuser",
                        "cognito:groups": ["user"],
                    }
                }
            }
        }
        mock_context = {"function_name": "test"}

        result = await middleware(handler_with_auth_check, event, mock_context)

        assert result["statusCode"] == 200
        assert result["body"] == "Hello testuser"
        assert result["user_roles"] == ["user"]

    @pytest.mark.anyio
    async def test_middleware_error_propagation(self, handler_with_auth_check):
        """Middleware should properly propagate authentication errors."""
        middleware = AuthenticationMiddleware()
        event = {"requestContext": {"authorizer": {"claims": {}}}}
        mock_context = {"function_name": "test"}

        with pytest.raises(AuthenticationError):
            await middleware(handler_with_auth_check, event, mock_context)

    @pytest.mark.anyio
    async def test_middleware_timeout_handling(self, handler_with_auth_check):
        """Middleware should respect timeout configuration."""
        middleware = AuthenticationMiddleware(timeout=0.001)  # Very short timeout
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "testuser",
                        "cognito:groups": ["user"],
                    }
                }
            }
        }
        mock_context = {"function_name": "test"}

        # This should work normally since auth is fast
        result = await middleware(handler_with_auth_check, event, mock_context)
        assert result["statusCode"] == 200
