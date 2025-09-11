"""
Unit tests for auth middleware functionality.

Tests cover:
- AuthContext authentication and authorization logic
- UnifiedIAMProvider user fetching and caching
- AuthMiddleware authentication flow and error handling
- Factory functions for different contexts
- Legacy compatibility functions
- Localstack development environment bypass
- Integration with error middleware
"""

import json
import os
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.shared_kernel.middleware.auth_middleware import (
    AuthContext,
    AuthMiddleware,
    AuthorizationError,
    UnifiedIAMProvider,
    get_current_user_legacy,
    iam_auth_middleware,
    optional_auth_middleware,
    products_auth_middleware,
    recipes_auth_middleware,
)

pytestmark = pytest.mark.anyio


class MockSeedUser:
    """Mock SeedUser object for testing."""

    def __init__(self, user_id: str | None = None, permissions: dict | None = None):
        self.user_id = user_id if user_id else str(uuid4())
        self.permissions = permissions if permissions is not None else {}

    def has_permission(self, *args) -> bool:
        """Mock permission checking."""
        if len(args) == 1:
            # Standard permission check
            permission = args[0]
            return permission in self.permissions.get("standard", [])
        if len(args) == 2:
            # Context-specific permission check
            context, permission = args
            return permission in self.permissions.get(context, [])
        return False


class TestAuthContext:
    """Test suite for AuthContext class."""

    def test_init_authenticated_user(self):
        """Test AuthContext initialization with authenticated user."""
        user_id = str(uuid4())
        mock_user = MockSeedUser(user_id)
        context = AuthContext(
            user_id=user_id,
            user_object=mock_user,
            is_authenticated=True,
            caller_context="products_catalog",
        )

        assert context.user_id == user_id
        assert context.user_object == mock_user
        assert context.user == mock_user
        assert context.is_authenticated is True
        assert context.caller_context == "products_catalog"

    def test_init_unauthenticated_user(self):
        """Test AuthContext initialization with unauthenticated user."""
        context = AuthContext(
            user_id="anonymous", user_object=None, is_authenticated=False
        )

        assert context.user_id == "anonymous"
        assert context.user_object is None
        assert context.user is None
        assert context.is_authenticated is False
        assert context.caller_context is None

    def test_has_permission_authenticated_user(self):
        """Test permission checking for authenticated user."""
        user_id = str(uuid4())
        mock_user = MockSeedUser(
            user_id,
            permissions={
                "standard": ["read_products", "write_products"],
                "admin_context": ["manage_users"],
            },
        )

        context = AuthContext(
            user_id=user_id, user_object=mock_user, is_authenticated=True
        )

        # Standard permission check
        assert context.has_permission("read_products") is True
        assert context.has_permission("delete_products") is False

        # Context-specific permission check
        assert context.has_permission("manage_users", "admin_context") is True
        assert context.has_permission("manage_users", "user_context") is False

    def test_has_permission_unauthenticated_user(self):
        """Test permission checking for unauthenticated user."""
        context = AuthContext(
            user_id="anonymous", user_object=None, is_authenticated=False
        )

        assert context.has_permission("read_products") is False
        assert context.has_permission("manage_users", "admin_context") is False

    def test_has_permission_no_user_object(self):
        """Test permission checking when user object is None."""
        user_id = str(uuid4())
        context = AuthContext(user_id=user_id, user_object=None, is_authenticated=True)

        assert context.has_permission("read_products") is False

    def test_is_owner_or_has_permission_owner(self):
        """Test owner-or-permission check when user is owner."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        mock_user = MockSeedUser(user_id, permissions={"standard": []})

        context = AuthContext(
            user_id=user_id, user_object=mock_user, is_authenticated=True
        )

        assert context.is_owner_or_has_permission(user_id, "admin") is True
        assert context.is_owner_or_has_permission(other_user_id, "admin") is False

    def test_is_owner_or_has_permission_permission(self):
        """Test owner-or-permission check when user has permission."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        mock_user = MockSeedUser(user_id, permissions={"standard": ["admin"]})

        context = AuthContext(
            user_id=user_id, user_object=mock_user, is_authenticated=True
        )

        assert context.is_owner_or_has_permission(other_user_id, "admin") is True
        assert context.is_owner_or_has_permission(other_user_id, "super_admin") is False

    def test_is_owner_or_has_permission_unauthenticated(self):
        """Test owner-or-permission check for unauthenticated user."""
        context = AuthContext(
            user_id="anonymous", user_object=None, is_authenticated=False
        )

        assert context.is_owner_or_has_permission("anonymous", "admin") is False


class TestUnifiedIAMProvider:
    """Test suite for UnifiedIAMProvider class."""

    @pytest.fixture
    def iam_provider(self):
        """Create IAM provider for testing."""
        return UnifiedIAMProvider("test_iam")

    async def test_get_user_success(self, async_pg_session: AsyncSession, iam_provider):
        """Test successful user retrieval with real database setup."""
        from datetime import datetime

        from sqlalchemy import text

        # Create test user ID
        user_id = str(uuid4())

        # Insert user and role data directly using SQL
        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.roles (name, context, permissions) 
            VALUES ('test_user', 'recipes_catalog', 'access_basic_features, access_developer_tools')
            ON CONFLICT (name, context) DO NOTHING
        """
            )
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.users (id, discarded, version, created_at, updated_at)
            VALUES (:user_id, false, 1, :created_at, :updated_at)
        """
            ),
            {
                "user_id": user_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.user_role_association (user_id, role_name, role_context)
            VALUES (:user_id, 'test_user', 'recipes_catalog')
        """
            ),
            {"user_id": user_id},
        )

        await async_pg_session.commit()

        # Call the real IAM provider (no mocking)
        result = await iam_provider.get_user(user_id, "recipes_catalog")

        # Verify the result
        assert result["statusCode"] == 200
        assert hasattr(result["body"], "id")
        assert result["body"].id == user_id

        # Verify the user has the expected role and permissions
        user = result["body"]
        assert len(user.roles) == 1
        role = list(user.roles)[0]
        assert role.name == "test_user"
        assert "access_basic_features" in role.permissions
        assert "access_developer_tools" in role.permissions

    @patch("src.contexts.iam.core.endpoints.internal.get.get")
    async def test_get_user_not_found(self, mock_get, iam_provider):
        """Test user not found scenario."""
        mock_get.return_value = {
            "statusCode": 404,
            "body": json.dumps({"message": "User not found"}),
        }

        unknown_user_id = str(uuid4())
        result = await iam_provider.get_user(unknown_user_id, "products_catalog")

        assert result["statusCode"] == 404

    async def test_get_user_caching(self, async_pg_session: AsyncSession, iam_provider):
        """Test request-scoped caching functionality with real database setup."""
        from datetime import datetime

        from sqlalchemy import text

        # Create test user ID
        user_id = str(uuid4())

        # Insert user and role data directly using SQL (same as test_get_user_success)
        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.roles (name, context, permissions) 
            VALUES ('cache_test_user', 'recipes_catalog', 'access_basic_features, access_developer_tools')
            ON CONFLICT (name, context) DO NOTHING
        """
            )
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.users (id, discarded, version, created_at, updated_at)
            VALUES (:user_id, false, 1, :created_at, :updated_at)
        """
            ),
            {
                "user_id": user_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.user_role_association (user_id, role_name, role_context)
            VALUES (:user_id, 'cache_test_user', 'recipes_catalog')
        """
            ),
            {"user_id": user_id},
        )

        await async_pg_session.commit()

        # First call - should hit database and cache the result
        result1 = await iam_provider.get_user(user_id, "recipes_catalog")
        # Second call with same parameters - should use cached result
        result2 = await iam_provider.get_user(user_id, "recipes_catalog")

        # Verify both calls succeeded
        assert result1["statusCode"] == result2["statusCode"] == 200
        assert hasattr(result1["body"], "id")
        assert hasattr(result2["body"], "id")
        assert result1["body"].id == result2["body"].id == user_id

        # Verify the cached result is the exact same object (identity check)
        assert result1["body"] is result2["body"]

        # Verify both results have the expected role and permissions
        for result in [result1, result2]:
            user = result["body"]
            assert len(user.roles) == 1
            role = list(user.roles)[0]
            assert role.name == "cache_test_user"
            assert "access_basic_features" in role.permissions
            assert "access_developer_tools" in role.permissions

    async def test_get_user_cache_different_contexts(
        self, async_pg_session: AsyncSession, iam_provider
    ):
        """Test caching with different contexts using real database setup."""
        from datetime import datetime

        from sqlalchemy import text

        # Create test user ID
        user_id = str(uuid4())

        # Insert user and role data for both products and recipes contexts
        # Use valid IAM permissions only
        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.roles (name, context, permissions) 
            VALUES 
                ('products_reader', 'products_catalog', 'access_basic_features, access_developer_tools'),
                ('recipes_reader', 'recipes_catalog', 'access_basic_features, access_support')
            ON CONFLICT (name, context) DO NOTHING
        """
            )
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.users (id, discarded, version, created_at, updated_at)
            VALUES (:user_id, false, 1, :created_at, :updated_at)
        """
            ),
            {
                "user_id": user_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.user_role_association (user_id, role_name, role_context)
            VALUES 
                (:user_id, 'products_reader', 'products_catalog'),
                (:user_id, 'recipes_reader', 'recipes_catalog')
        """
            ),
            {"user_id": user_id},
        )

        await async_pg_session.commit()

        # Call with different contexts - each should create separate cache entries
        result1 = await iam_provider.get_user(user_id, "products_catalog")
        result2 = await iam_provider.get_user(user_id, "recipes_catalog")

        # Both calls should succeed
        assert result1["statusCode"] == result2["statusCode"] == 200
        assert result1["body"].id == result2["body"].id == user_id

        # Results should be different objects (different cache entries for different contexts)
        assert result1["body"] is not result2["body"]

        # Verify cache has two entries (different contexts create different cache keys)
        assert len(iam_provider._cache) == 2

        # Verify cache keys contain context information
        cache_keys = list(iam_provider._cache.keys())
        assert any("products_catalog" in key for key in cache_keys)
        assert any("recipes_catalog" in key for key in cache_keys)

        # Call same contexts again - should use cached results
        result1_cached = await iam_provider.get_user(user_id, "products_catalog")
        result2_cached = await iam_provider.get_user(user_id, "recipes_catalog")

        # Should return same cached objects
        assert result1["body"] is result1_cached["body"]
        assert result2["body"] is result2_cached["body"]

        # Cache should still have only 2 entries
        assert len(iam_provider._cache) == 2

    async def test_role_context_isolation(
        self, async_pg_session: AsyncSession, iam_provider
    ):
        """Test that roles from different contexts are properly isolated."""
        from datetime import datetime

        from sqlalchemy import text

        # Create test user ID
        user_id = str(uuid4())

        # Insert user and role data for multiple contexts with different permissions
        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.roles (name, context, permissions) 
            VALUES 
                ('products_admin', 'products_catalog', 'access_basic_features, access_developer_tools, manage_users'),
                ('recipes_viewer', 'recipes_catalog', 'access_basic_features, access_support, view_audit_log')
            ON CONFLICT (name, context) DO NOTHING
        """
            )
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.users (id, discarded, version, created_at, updated_at)
            VALUES (:user_id, false, 1, :created_at, :updated_at)
        """
            ),
            {
                "user_id": user_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        )

        await async_pg_session.execute(
            text(
                """
            INSERT INTO iam.user_role_association (user_id, role_name, role_context)
            VALUES 
                (:user_id, 'products_admin', 'products_catalog'),
                (:user_id, 'recipes_viewer', 'recipes_catalog')
        """
            ),
            {"user_id": user_id},
        )

        await async_pg_session.commit()

        # Get user in products context
        products_result = await iam_provider.get_user(user_id, "products_catalog")
        products_user = products_result["body"]

        # Get user in recipes context
        recipes_result = await iam_provider.get_user(user_id, "recipes_catalog")
        recipes_user = recipes_result["body"]

        # Verify all calls succeeded
        assert products_result["statusCode"] == 200
        assert recipes_result["statusCode"] == 200

        # Verify context isolation: each context should only get 1 role (its own)
        assert len(products_user.roles) == 1
        assert len(recipes_user.roles) == 1

        # Get the roles
        products_role = list(products_user.roles)[0]
        recipes_role = list(recipes_user.roles)[0]

        # Verify each context gets the correct role name
        assert products_role.name == "products_admin"
        assert recipes_role.name == "recipes_viewer"

        # Verify each context gets different role classes (context-specific)
        assert "products_catalog" in str(type(products_role))
        assert "recipes_catalog" in str(type(recipes_role))

        # Verify permission isolation: each role only has its context-specific permissions

        # Products context permissions
        assert "access_basic_features" in products_role.permissions
        assert "access_developer_tools" in products_role.permissions
        assert "manage_users" in products_role.permissions
        # Should NOT have permissions from other contexts
        assert "access_support" not in products_role.permissions  # recipes permission
        assert "view_audit_log" not in products_role.permissions  # recipes permission

        # Recipes context permissions
        assert "access_basic_features" in recipes_role.permissions
        assert "access_support" in recipes_role.permissions
        assert "view_audit_log" in recipes_role.permissions
        # Should NOT have permissions from other contexts
        assert (
            "access_developer_tools" not in recipes_role.permissions
        )  # products permission
        assert "manage_users" not in recipes_role.permissions  # products permission

        # Verify that each result is a different object (proper context separation)
        assert products_user is not recipes_user

        # Verify each has different role objects
        assert products_role is not recipes_role

    async def test_unsupported_context_raises_error(self, iam_provider):
        """Test that unsupported caller contexts raise appropriate errors."""
        user_id = str(uuid4())

        # Test with unsupported context should raise error
        result = await iam_provider.get_user(user_id, "unsupported_context")
        assert result["statusCode"] == 500
        assert "Unsupported caller context" in result["body"]

        # Test with IAM context should also raise error (not supported in this provider)
        result = await iam_provider.get_user(user_id, "IAM")
        assert result["statusCode"] == 500
        assert "Unsupported caller context" in result["body"]

    def test_clear_cache(self, iam_provider):
        """Test cache clearing functionality."""
        # Add something to cache
        iam_provider._cache["test_key"] = "test_value"
        assert "test_key" in iam_provider._cache

        # Clear cache
        iam_provider.clear_cache()
        assert len(iam_provider._cache) == 0

    @patch("src.contexts.iam.core.endpoints.internal.get.get")
    async def test_get_user_exception_handling(self, mock_get, iam_provider):
        """Test exception handling in user retrieval."""
        mock_get.side_effect = Exception("IAM service error")

        user_id = str(uuid4())
        result = await iam_provider.get_user(user_id, "products_catalog")

        assert result["statusCode"] == 500
        # The error message should match what the IAM provider actually returns
        assert "Authentication service error" in result["body"]


class TestAuthMiddleware:
    """Test suite for AuthMiddleware class."""

    @pytest.fixture
    def auth_middleware(self):
        """Create auth middleware for testing."""
        return AuthMiddleware(
            caller_context="products_catalog", require_authentication=True
        )

    @pytest.fixture
    def optional_auth_middleware_instance(self):
        """Create optional auth middleware for testing."""
        return AuthMiddleware(
            caller_context="products_catalog", require_authentication=False
        )

    @pytest.fixture
    def lambda_event(self):
        """Create mock Lambda event."""
        user_id = str(uuid4())
        return {
            "requestContext": {"authorizer": {"claims": {"sub": user_id}}},
            "body": json.dumps({"test": "data"}),
        }

    @pytest.fixture
    def mock_handler(self):
        """Create mock endpoint handler."""

        async def handler(event):
            return {"statusCode": 200, "body": json.dumps({"message": "success"})}

        return handler

    @patch.dict(os.environ, {"IS_LOCALSTACK": "true"})
    async def test_localstack_bypass(self, auth_middleware, lambda_event, mock_handler):
        """Test Localstack environment bypass."""
        response = await auth_middleware(mock_handler, lambda_event)

        assert response["statusCode"] == 200
        assert auth_middleware._current_auth_context is None  # Cleared after request
        assert auth_middleware.iam_provider._cache == {}  # Cache cleared

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_successful_authentication(
        self, mock_get_user, auth_middleware, lambda_event, mock_handler
    ):
        """Test successful authentication flow."""
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(user_id)
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        response = await auth_middleware(mock_handler, lambda_event)

        assert response["statusCode"] == 200
        mock_get_user.assert_called_once_with(user_id, "products_catalog")

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_authentication_failure(
        self, mock_get_user, auth_middleware, lambda_event, mock_handler
    ):
        """Test authentication failure."""
        mock_get_user.return_value = {
            "statusCode": 401,
            "body": json.dumps({"message": "Invalid user"}),
        }

        response = await auth_middleware(mock_handler, lambda_event)

        assert response["statusCode"] == 401

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    async def test_missing_user_id(self, auth_middleware, mock_handler):
        """Test authentication with missing user ID."""
        event_no_user = {"requestContext": {"authorizer": {}}}

        response = await auth_middleware(mock_handler, event_no_user)

        assert response["statusCode"] == 401

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_optional_authentication_success(
        self,
        mock_get_user,
        optional_auth_middleware_instance,
        lambda_event,
        mock_handler,
    ):
        """Test optional authentication with valid user."""
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(user_id)
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        response = await optional_auth_middleware_instance(mock_handler, lambda_event)

        assert response["statusCode"] == 200

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    async def test_optional_authentication_no_user(
        self, optional_auth_middleware_instance, mock_handler
    ):
        """Test optional authentication with missing user."""
        event_no_user = {"requestContext": {"authorizer": {}}}

        response = await optional_auth_middleware_instance(mock_handler, event_no_user)

        assert response["statusCode"] == 200  # Should still proceed

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_authorization_error_handling(
        self, mock_get_user, auth_middleware, lambda_event
    ):
        """Test authorization error handling."""
        # Mock successful authentication first
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(user_id)
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        async def handler_with_auth_error(event):
            raise AuthorizationError("Insufficient permissions")

        response = await auth_middleware(handler_with_auth_error, lambda_event)

        assert response["statusCode"] == 403

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_other_exception_propagation(
        self, mock_get_user, auth_middleware, lambda_event
    ):
        """Test that non-auth exceptions are propagated."""
        # Mock successful authentication first
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(user_id)
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        async def handler_with_error(event):
            raise ValueError("Some other error")

        with pytest.raises(ValueError, match="Some other error"):
            await auth_middleware(handler_with_error, lambda_event)

    def test_current_user_property(self, auth_middleware):
        """Test current_user property access."""
        # Initially no context
        assert auth_middleware.current_user is None

        # Set mock context
        user_id = str(uuid4())
        mock_context = AuthContext(user_id, is_authenticated=True)
        auth_middleware._current_auth_context = mock_context

        assert auth_middleware.current_user == mock_context


class TestFactoryFunctions:
    """Test suite for auth middleware factory functions."""

    def test_products_auth_middleware(self):
        """Test products auth middleware factory."""
        middleware = products_auth_middleware()

        assert isinstance(middleware, AuthMiddleware)
        assert middleware.caller_context == "products_catalog"
        assert middleware.require_authentication is True

    def test_recipes_auth_middleware(self):
        """Test recipes auth middleware factory."""
        middleware = recipes_auth_middleware()

        assert isinstance(middleware, AuthMiddleware)
        assert middleware.caller_context == "recipes_catalog"
        assert middleware.require_authentication is True

    def test_iam_auth_middleware(self):
        """Test IAM auth middleware factory."""
        middleware = iam_auth_middleware()

        assert isinstance(middleware, AuthMiddleware)
        assert (
            middleware.caller_context == "recipes_catalog"
        )  # IAM operations use recipes_catalog context
        assert middleware.require_authentication is True

    def test_optional_auth_middleware(self):
        """Test optional auth middleware factory."""
        middleware = optional_auth_middleware("custom_context")

        assert isinstance(middleware, AuthMiddleware)
        assert middleware.caller_context == "custom_context"
        assert middleware.require_authentication is False


class TestLegacyCompatibility:
    """Test suite for legacy compatibility functions."""

    @pytest.fixture
    def lambda_event(self):
        """Create mock Lambda event."""
        user_id = str(uuid4())
        return {"requestContext": {"authorizer": {"claims": {"sub": user_id}}}}

    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_get_current_user_legacy_success(self, mock_get_user, lambda_event):
        """Test legacy user retrieval function - success."""
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(user_id)
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        result = await get_current_user_legacy(lambda_event, "products_catalog")

        assert result["statusCode"] == 200
        assert result["body"] == mock_user
        mock_get_user.assert_called_once_with(user_id, "products_catalog")

    async def test_get_current_user_legacy_no_user_id(self):
        """Test legacy user retrieval function - missing user ID."""
        event_no_user = {"requestContext": {"authorizer": {}}}

        result = await get_current_user_legacy(event_no_user, "products_catalog")

        assert result["statusCode"] == 401
        assert "User ID not found" in result["body"]

    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_get_current_user_legacy_exception(self, mock_get_user, lambda_event):
        """Test legacy user retrieval function - exception handling."""
        mock_get_user.side_effect = Exception("IAM error")

        result = await get_current_user_legacy(lambda_event, "products_catalog")

        assert result["statusCode"] == 500
        assert "Authentication error" in result["body"]


class TestAuthIntegration:
    """Integration tests for auth middleware."""

    @pytest.fixture
    def lambda_event(self):
        """Create mock Lambda event."""
        user_id = str(uuid4())
        resource_id = str(uuid4())
        return {
            "requestContext": {"authorizer": {"claims": {"sub": user_id}}},
            "pathParameters": {"id": resource_id},
            "body": json.dumps({"data": "test"}),
        }

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_full_auth_flow_with_permission_check(
        self, mock_get_user, lambda_event
    ):
        """Test complete authentication and authorization flow."""
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(
            user_id, permissions={"standard": ["read_products", "write_products"]}
        )
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        middleware = products_auth_middleware()

        async def protected_handler(event):
            # Simulate permission checking in handler
            auth_context = middleware.current_user
            if not auth_context or not auth_context.has_permission("read_products"):
                raise AuthorizationError("Permission denied")

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {"message": "success", "user": auth_context.user_id}
                ),
            }

        response = await middleware(protected_handler, lambda_event)

        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["user"] == user_id
        assert response_body["message"] == "success"

    @patch.dict(os.environ, {"IS_LOCALSTACK": "false"})
    @patch.object(UnifiedIAMProvider, "get_user")
    async def test_owner_or_permission_flow(self, mock_get_user, lambda_event):
        """Test owner-or-permission authorization pattern."""
        user_id = lambda_event["requestContext"]["authorizer"]["claims"]["sub"]
        mock_user = MockSeedUser(user_id, permissions={"standard": []})
        mock_get_user.return_value = {"statusCode": 200, "body": mock_user}

        middleware = products_auth_middleware()

        async def owner_protected_handler(event):
            auth_context = middleware.current_user
            resource_owner_id = event.get("pathParameters", {}).get("id")

            # Simulate owner check (user trying to access resource with different ID)
            if not auth_context or not auth_context.is_owner_or_has_permission(
                resource_owner_id, "admin"
            ):
                raise AuthorizationError("Access denied")

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "access granted"}),
            }

        # This should fail since user_id != resource_id and no admin permission
        response = await middleware(owner_protected_handler, lambda_event)

        assert response["statusCode"] == 403
