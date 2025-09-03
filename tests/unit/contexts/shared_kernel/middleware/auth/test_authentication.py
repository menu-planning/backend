"""Unit tests for authentication middleware.

Tests the authentication middleware behavior with fakes and mocks,
focusing on business logic and orchestration without I/O dependencies.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

import pytest
from pytest import fixture

from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthenticationError,
    AuthenticationMiddleware,
    AuthenticationStrategy,
    AuthorizationError,
    AuthContext,
    AuthPolicy,
    AWSLambdaAuthenticationStrategy,
    UnifiedIAMProvider,
    create_auth_middleware,
    products_aws_auth_middleware,
    recipes_aws_auth_middleware,
    client_onboarding_aws_auth_middleware,
    AUTHENTICATION_REQUIRED_MSG,
    INSUFFICIENT_PERMISSIONS_MSG,
    HTTP_OK,
    HTTP_INTERNAL_SERVER_ERROR,
)


# Test fixtures
@fixture
def fake_iam_provider():
    """Fake IAM provider for testing."""
    provider = MagicMock(spec=UnifiedIAMProvider)
    provider.get_user = AsyncMock()
    provider.clear_cache = MagicMock()
    return provider


@fixture
def fake_strategy():
    """Fake authentication strategy for testing."""
    strategy = MagicMock(spec=AuthenticationStrategy)
    strategy.extract_auth_context = AsyncMock()
    strategy.get_request_data = MagicMock()
    strategy.inject_auth_context = MagicMock()
    strategy.cleanup = AsyncMock()
    return strategy


@fixture
def fake_handler():
    """Fake endpoint handler for testing."""
    handler = AsyncMock()
    handler.return_value = {"statusCode": 200, "body": "success"}
    return handler


@fixture
def sample_event():
    """Sample AWS Lambda event for testing."""
    return {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "user123",
                    "custom:roles": "admin,user",
                    "cognito:groups": ["admin", "user"],
                }
            }
        },
        "body": '{"test": "data"}',
    }


@fixture
def sample_context():
    """Sample AWS Lambda context for testing."""
    context = MagicMock()
    context.function_name = "test-function"
    context.request_id = "req-123"
    return context


# AuthPolicy tests
class TestAuthPolicy:
    """Test AuthPolicy behavior and validation logic."""

    def test_auth_policy_defaults(self):
        """Test AuthPolicy with default values."""
        policy = AuthPolicy()
        
        assert policy.require_authentication is True
        assert policy.allowed_roles == []
        assert policy.caller_context is None

    def test_auth_policy_custom_values(self):
        """Test AuthPolicy with custom values."""
        policy = AuthPolicy(
            require_authentication=False,
            allowed_roles=["admin", "user"],
            caller_context="test_context"
        )
        
        assert policy.require_authentication is False
        assert policy.allowed_roles == ["admin", "user"]
        assert policy.caller_context == "test_context"

    def test_is_authenticated_required_true(self):
        """Test is_authenticated_required returns True when required."""
        policy = AuthPolicy(require_authentication=True)
        assert policy.is_authenticated_required() is True

    def test_is_authenticated_required_false(self):
        """Test is_authenticated_required returns False when not required."""
        policy = AuthPolicy(require_authentication=False)
        assert policy.is_authenticated_required() is False

    def test_has_required_role_no_restrictions(self):
        """Test has_required_role with no role restrictions."""
        policy = AuthPolicy(allowed_roles=None)
        user_roles = ["admin", "user"]
        
        assert policy.has_required_role(user_roles) is True

    def test_has_required_role_empty_restrictions(self):
        """Test has_required_role with empty role restrictions."""
        policy = AuthPolicy(allowed_roles=[])
        user_roles = ["admin", "user"]
        
        assert policy.has_required_role(user_roles) is True

    def test_has_required_role_user_has_role(self):
        """Test has_required_role when user has required role."""
        policy = AuthPolicy(allowed_roles=["admin"])
        user_roles = ["admin", "user"]
        
        assert policy.has_required_role(user_roles) is True

    def test_has_required_role_user_lacks_role(self):
        """Test has_required_role when user lacks required role."""
        policy = AuthPolicy(allowed_roles=["admin"])
        user_roles = ["user"]
        
        assert policy.has_required_role(user_roles) is False

    def test_has_required_role_multiple_roles(self):
        """Test has_required_role with multiple allowed roles."""
        policy = AuthPolicy(allowed_roles=["admin", "moderator"])
        user_roles = ["user", "moderator"]
        
        assert policy.has_required_role(user_roles) is True


# AuthContext tests
class TestAuthContext:
    """Test AuthContext behavior and permission checking."""

    def test_auth_context_defaults(self):
        """Test AuthContext with default values."""
        context = AuthContext()
        
        assert context.user_id is None
        assert context.user_roles == []
        assert context.is_authenticated is False
        assert context.metadata == {}
        assert context.user_object is None
        assert context.caller_context is None

    def test_auth_context_custom_values(self):
        """Test AuthContext with custom values."""
        user_object = MagicMock()
        context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=True,
            metadata={"key": "value"},
            user_object=user_object,
            caller_context="test_context"
        )
        
        assert context.user_id == "user123"
        assert context.user_roles == ["admin"]
        assert context.is_authenticated is True
        assert context.metadata == {"key": "value"}
        assert context.user_object == user_object
        assert context.caller_context == "test_context"

    def test_has_role_true(self):
        """Test has_role returns True when user has role."""
        context = AuthContext(user_roles=["admin", "user"])
        assert context.has_role("admin") is True

    def test_has_role_false(self):
        """Test has_role returns False when user lacks role."""
        context = AuthContext(user_roles=["user"])
        assert context.has_role("admin") is False

    def test_has_any_role_true(self):
        """Test has_any_role returns True when user has any role."""
        context = AuthContext(user_roles=["user"])
        assert context.has_any_role(["admin", "user"]) is True

    def test_has_any_role_false(self):
        """Test has_any_role returns False when user has no roles."""
        context = AuthContext(user_roles=["guest"])
        assert context.has_any_role(["admin", "user"]) is False

    def test_has_permission_with_user_object(self):
        """Test has_permission with user object."""
        user_object = MagicMock()
        user_object.has_permission.return_value = True
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        result = context.has_permission("read")
        assert result is True
        user_object.has_permission.assert_called_once_with("read")

    def test_has_permission_with_context(self):
        """Test has_permission with context."""
        user_object = MagicMock()
        user_object.has_permission.return_value = True
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        result = context.has_permission("read", "products")
        assert result is True
        user_object.has_permission.assert_called_once_with("products", "read")

    def test_has_permission_not_authenticated(self):
        """Test has_permission when not authenticated."""
        context = AuthContext(is_authenticated=False)
        assert context.has_permission("read") is False

    def test_has_permission_no_user_object(self):
        """Test has_permission when no user object."""
        context = AuthContext(is_authenticated=True, user_object=None)
        assert context.has_permission("read") is False

    def test_is_owner_or_has_permission_owner(self):
        """Test is_owner_or_has_permission when user is owner."""
        context = AuthContext(user_id="user123", is_authenticated=True)
        assert context.is_owner_or_has_permission("user123", "read") is True

    def test_is_owner_or_has_permission_has_permission(self):
        """Test is_owner_or_has_permission when user has permission."""
        user_object = MagicMock()
        user_object.has_permission.return_value = True
        context = AuthContext(
            user_id="user123",
            is_authenticated=True,
            user_object=user_object
        )
        
        assert context.is_owner_or_has_permission("other123", "read") is True

    def test_is_owner_or_has_permission_neither(self):
        """Test is_owner_or_has_permission when user is neither owner nor has permission."""
        user_object = MagicMock()
        user_object.has_permission.return_value = False
        context = AuthContext(
            user_id="user123",
            is_authenticated=True,
            user_object=user_object
        )
        
        assert context.is_owner_or_has_permission("other123", "read") is False

    def test_user_property(self):
        """Test user property returns user_object."""
        user_object = MagicMock()
        context = AuthContext(user_object=user_object)
        assert context.user == user_object

    def test_repr(self):
        """Test string representation of AuthContext."""
        context = AuthContext(
            user_id="user123",
            is_authenticated=True,
            user_roles=["admin"]
        )
        
        repr_str = repr(context)
        assert "user123" in repr_str
        assert "True" in repr_str
        assert "admin" in repr_str


# UnifiedIAMProvider tests
class TestUnifiedIAMProvider:
    """Test UnifiedIAMProvider behavior with fakes."""

    def test_iam_provider_defaults(self):
        """Test UnifiedIAMProvider with default values."""
        provider = UnifiedIAMProvider()
        
        assert provider.cache_strategy == "request"
        assert provider._cache == {}
        assert provider._cache_stats == {"hits": 0, "misses": 0}

    def test_iam_provider_custom_strategy(self):
        """Test UnifiedIAMProvider with custom cache strategy."""
        provider = UnifiedIAMProvider(
            logger_name="test_iam",
            cache_strategy="container"
        )
        
        assert provider.cache_strategy == "container"
        assert provider._cache == {}
        assert provider._cache_stats == {"hits": 0, "misses": 0}

    @pytest.mark.anyio
    async def test_get_user_success(self, fake_iam_provider):
        """Test successful user retrieval."""
        user_data = {"id": "user123", "roles": ["admin"]}
        fake_iam_provider.get_user.return_value = {
            "statusCode": HTTP_OK,
            "body": user_data
        }
        
        result = await fake_iam_provider.get_user("user123", "products_catalog")
        
        assert result["statusCode"] == HTTP_OK
        assert result["body"] == user_data
        fake_iam_provider.get_user.assert_called_once_with("user123", "products_catalog")

    @pytest.mark.anyio
    async def test_get_user_error(self, fake_iam_provider):
        """Test user retrieval with error response."""
        fake_iam_provider.get_user.return_value = {
            "statusCode": HTTP_INTERNAL_SERVER_ERROR,
            "body": json.dumps({"message": "User not found"})
        }
        
        result = await fake_iam_provider.get_user("user123", "products_catalog")
        
        assert result["statusCode"] == HTTP_INTERNAL_SERVER_ERROR
        assert "User not found" in result["body"]

    def test_clear_cache_request_strategy(self):
        """Test cache clearing with request strategy."""
        provider = UnifiedIAMProvider(cache_strategy="request")
        provider._cache = {"user123:products_catalog": {"id": "user123"}}
        
        provider.clear_cache()
        
        assert provider._cache == {}

    def test_clear_cache_container_strategy(self):
        """Test cache clearing with container strategy."""
        provider = UnifiedIAMProvider(cache_strategy="container")
        provider._cache = {"user123:products_catalog": {"id": "user123"}}
        
        provider.clear_cache()
        
        # Cache should not be cleared with container strategy
        assert provider._cache == {"user123:products_catalog": {"id": "user123"}}

    def test_clear_cache_unknown_strategy(self):
        """Test cache clearing with unknown strategy defaults to clearing."""
        provider = UnifiedIAMProvider(cache_strategy="unknown")
        provider._cache = {"user123:products_catalog": {"id": "user123"}}
        
        provider.clear_cache()
        
        # Should default to clearing cache
        assert provider._cache == {}

    def test_get_cache_stats_empty(self):
        """Test cache statistics with no requests."""
        provider = UnifiedIAMProvider()
        
        stats = provider.get_cache_stats()
        
        assert stats["cache_strategy"] == "request"
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["cache_size"] == 0

    def test_get_cache_stats_with_data(self):
        """Test cache statistics with some requests."""
        provider = UnifiedIAMProvider()
        provider._cache_stats = {"hits": 8, "misses": 2}
        provider._cache = {"user1:context1": {}, "user2:context2": {}}
        
        stats = provider.get_cache_stats()
        
        assert stats["cache_strategy"] == "request"
        assert stats["cache_hits"] == 8
        assert stats["cache_misses"] == 2
        assert stats["total_requests"] == 10
        assert stats["hit_rate"] == 0.8
        assert stats["cache_size"] == 2

    def test_get_cache_hit_rate_percentage(self):
        """Test cache hit rate calculation as percentage."""
        provider = UnifiedIAMProvider()
        provider._cache_stats = {"hits": 3, "misses": 7}
        
        hit_rate = provider._get_cache_hit_rate()
        
        assert hit_rate == 30.0  # 3/10 * 100

    def test_get_cache_hit_rate_zero_requests(self):
        """Test cache hit rate with no requests."""
        provider = UnifiedIAMProvider()
        provider._cache_stats = {"hits": 0, "misses": 0}
        
        hit_rate = provider._get_cache_hit_rate()
        
        assert hit_rate == 0.0


# AWSLambdaAuthenticationStrategy tests
class TestAWSLambdaAuthenticationStrategy:
    """Test AWS Lambda authentication strategy behavior."""

    @pytest.mark.anyio
    async def test_extract_auth_context_valid_token(self, fake_iam_provider, sample_event, sample_context):
        """Test extracting auth context with valid token."""
        # Setup
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        user_data = {"id": "user123", "roles": ["admin"]}
        fake_iam_provider.get_user.return_value = {
            "statusCode": HTTP_OK,
            "body": user_data
        }
        
        # Execute
        auth_context = await strategy.extract_auth_context(sample_event, sample_context)
        
        # Verify
        assert auth_context.user_id == "user123"
        assert set(auth_context.user_roles) == {"admin", "user"}
        assert len(auth_context.user_roles) == 2
        assert auth_context.is_authenticated is True
        assert auth_context.caller_context == "products_catalog"
        assert auth_context.user_object == user_data
        assert "authorizer" in auth_context.metadata
        assert "claims" in auth_context.metadata
        assert auth_context.metadata["function_name"] == "test-function"
        assert auth_context.metadata["request_id"] == "req-123"

    @pytest.mark.anyio
    async def test_extract_auth_context_invalid_token(self, fake_iam_provider):
        """Test extracting auth context with invalid token."""
        # Setup
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {"claims": {}}}}
        context = MagicMock()
        
        # Execute
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Verify
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_missing_token(self, fake_iam_provider):
        """Test extracting auth context with missing token."""
        # Setup
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {}}
        context = MagicMock()
        
        # Execute
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Verify
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    def test_get_request_data_positional_args(self, fake_iam_provider, sample_event, sample_context):
        """Test getting request data from positional arguments."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        event, context = strategy.get_request_data(sample_event, sample_context)
        
        assert event == sample_event
        assert context == sample_context

    def test_get_request_data_keyword_args(self, fake_iam_provider, sample_event, sample_context):
        """Test getting request data from keyword arguments."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        event, context = strategy.get_request_data(event=sample_event, context=sample_context)
        
        assert event == sample_event
        assert context == sample_context

    def test_get_request_data_missing_args(self, fake_iam_provider):
        """Test getting request data with missing arguments."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        with pytest.raises(IndexError):
            strategy.get_request_data()

    def test_inject_auth_context(self, fake_iam_provider, sample_event):
        """Test injecting auth context into request data."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        auth_context = AuthContext(user_id="user123", is_authenticated=True)
        
        strategy.inject_auth_context(sample_event, auth_context)
        
        assert sample_event["_auth_context"] == auth_context

    def test_extract_user_roles_custom_roles(self, fake_iam_provider):
        """Test extracting user roles from custom claims."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": "admin,user,moderator"}
        
        roles = strategy._extract_user_roles(claims)
        
        # The order may vary due to set() conversion, so check that all roles are present
        assert set(roles) == {"admin", "user", "moderator"}
        assert len(roles) == 3

    def test_extract_user_roles_cognito_groups(self, fake_iam_provider):
        """Test extracting user roles from cognito groups."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"cognito:groups": ["admin", "user"]}
        
        roles = strategy._extract_user_roles(claims)
        
        # The order may vary due to set() conversion, so check that all roles are present
        assert set(roles) == {"admin", "user"}
        assert len(roles) == 2

    def test_extract_user_roles_scope(self, fake_iam_provider):
        """Test extracting user roles from OAuth scope."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"scope": "read write admin"}
        
        roles = strategy._extract_user_roles(claims)
        
        # The order may vary due to set() conversion, so check that all roles are present
        assert set(roles) == {"read", "write", "admin"}
        assert len(roles) == 3

    def test_extract_user_roles_duplicates(self, fake_iam_provider):
        """Test extracting user roles removes duplicates."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {
            "custom:roles": "admin,user",
            "cognito:groups": ["admin", "moderator"]
        }
        
        roles = strategy._extract_user_roles(claims)
        
        assert set(roles) == {"admin", "user", "moderator"}

    @pytest.mark.anyio
    async def test_cleanup(self, fake_iam_provider):
        """Test cleanup method."""
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        await strategy.cleanup()
        
        fake_iam_provider.clear_cache.assert_called_once()


# AuthenticationMiddleware tests
class TestAuthenticationMiddleware:
    """Test AuthenticationMiddleware behavior and orchestration."""

    @pytest.mark.anyio
    async def test_authentication_middleware_valid_token(self, fake_strategy, fake_handler):
        """Test authentication middleware with valid token."""
        # Setup
        auth_context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=True
        )
        fake_strategy.extract_auth_context.return_value = auth_context
        fake_strategy.get_request_data.return_value = ({"test": "data"}, "context")
        
        policy = AuthPolicy(require_authentication=True, allowed_roles=["admin"])
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute
        result = await middleware(fake_handler, "event", "context")
        
        # Verify
        assert result == {"statusCode": 200, "body": "success"}
        fake_strategy.extract_auth_context.assert_called_once_with("event", "context")
        fake_strategy.get_request_data.assert_called_once_with("event", "context")
        fake_strategy.inject_auth_context.assert_called_once()
        fake_handler.assert_called_once()
        fake_strategy.cleanup.assert_called_once()

    @pytest.mark.anyio
    async def test_authentication_middleware_invalid_token(self, fake_strategy, fake_handler):
        """Test authentication middleware with invalid token."""
        # Setup
        auth_context = AuthContext(is_authenticated=False)
        fake_strategy.extract_auth_context.return_value = auth_context
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, "event", "context")
        
        fake_strategy.extract_auth_context.assert_called_once()
        fake_strategy.cleanup.assert_called_once()

    @pytest.mark.anyio
    async def test_authentication_middleware_expired_token(self, fake_strategy, fake_handler):
        """Test authentication middleware with expired token."""
        # Setup
        auth_context = AuthContext(
            user_id="user123",
            is_authenticated=False  # Expired token results in not authenticated
        )
        fake_strategy.extract_auth_context.return_value = auth_context
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, "event", "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_missing_token(self, fake_strategy, fake_handler):
        """Test authentication middleware with missing token."""
        # Setup
        auth_context = AuthContext(is_authenticated=False)
        fake_strategy.extract_auth_context.return_value = auth_context
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, "event", "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_async_behavior(self, fake_strategy, fake_handler):
        """Test authentication middleware async behavior."""
        # Setup
        auth_context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=True
        )
        fake_strategy.extract_auth_context.return_value = auth_context
        fake_strategy.get_request_data.return_value = ({"test": "data"}, "context")
        
        policy = AuthPolicy(require_authentication=True, allowed_roles=["admin"])
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute
        result = await middleware(fake_handler, "event", "context")
        
        # Verify async behavior
        assert result == {"statusCode": 200, "body": "success"}
        fake_strategy.extract_auth_context.assert_called_once()
        fake_strategy.cleanup.assert_called_once()

    @pytest.mark.anyio
    async def test_authentication_middleware_insufficient_permissions(self, fake_strategy, fake_handler):
        """Test authentication middleware with insufficient permissions."""
        # Setup
        auth_context = AuthContext(
            user_id="user123",
            user_roles=["user"],  # User doesn't have admin role
            is_authenticated=True
        )
        fake_strategy.extract_auth_context.return_value = auth_context
        
        policy = AuthPolicy(require_authentication=True, allowed_roles=["admin"])
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(AuthorizationError, match=INSUFFICIENT_PERMISSIONS_MSG):
            await middleware(fake_handler, "event", "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_no_auth_required(self, fake_strategy, fake_handler):
        """Test authentication middleware when authentication is not required."""
        # Setup
        auth_context = AuthContext(is_authenticated=False)
        fake_strategy.extract_auth_context.return_value = auth_context
        fake_strategy.get_request_data.return_value = ({"test": "data"}, "context")
        
        policy = AuthPolicy(require_authentication=False)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute
        result = await middleware(fake_handler, "event", "context")
        
        # Verify
        assert result == {"statusCode": 200, "body": "success"}
        fake_strategy.extract_auth_context.assert_called_once()
        fake_strategy.inject_auth_context.assert_called_once()

    @pytest.mark.anyio
    async def test_authentication_middleware_cleanup_on_error(self, fake_strategy, fake_handler):
        """Test that cleanup is called even when authentication fails."""
        # Setup
        auth_context = AuthContext(is_authenticated=False)
        fake_strategy.extract_auth_context.return_value = auth_context
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(AuthenticationError):
            await middleware(fake_handler, "event", "context")
        
        fake_strategy.cleanup.assert_called_once()

    def test_get_auth_context(self, fake_strategy):
        """Test getting auth context from request data."""
        middleware = AuthenticationMiddleware(strategy=fake_strategy)
        auth_context = AuthContext(user_id="user123")
        request_data = {"_auth_context": auth_context}
        
        result = middleware.get_auth_context(request_data)
        
        assert result == auth_context

    def test_get_auth_context_not_found(self, fake_strategy):
        """Test getting auth context when not present."""
        middleware = AuthenticationMiddleware(strategy=fake_strategy)
        request_data = {}
        
        result = middleware.get_auth_context(request_data)
        
        assert result is None


# Factory function tests
class TestFactoryFunctions:
    """Test factory functions for creating authentication middleware."""

    def test_create_auth_middleware_defaults(self, fake_strategy):
        """Test create_auth_middleware with default values."""
        middleware = create_auth_middleware(strategy=fake_strategy)
        
        assert isinstance(middleware, AuthenticationMiddleware)
        assert middleware.strategy == fake_strategy
        assert middleware.policy.require_authentication is True
        assert middleware.policy.allowed_roles == []
        assert middleware.policy.caller_context is None

    def test_create_auth_middleware_custom_values(self, fake_strategy):
        """Test create_auth_middleware with custom values."""
        middleware = create_auth_middleware(
            strategy=fake_strategy,
            require_authentication=False,
            allowed_roles=["admin"],
            caller_context="test_context",
            name="test_middleware",
            timeout=30.0
        )
        
        assert isinstance(middleware, AuthenticationMiddleware)
        assert middleware.strategy == fake_strategy
        assert middleware.policy.require_authentication is False
        assert middleware.policy.allowed_roles == ["admin"]
        assert middleware.policy.caller_context == "test_context"
        assert middleware.name == "test_middleware"
        assert middleware.timeout == 30.0

    @patch('src.contexts.shared_kernel.middleware.auth.authentication.UnifiedIAMProvider')
    @patch('src.contexts.shared_kernel.middleware.auth.authentication.AWSLambdaAuthenticationStrategy')
    def test_products_aws_auth_middleware(self, mock_strategy_class, mock_provider_class):
        """Test products AWS auth middleware factory."""
        mock_provider = MagicMock()
        mock_strategy = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_strategy_class.return_value = mock_strategy
        
        middleware = products_aws_auth_middleware()
        
        assert isinstance(middleware, AuthenticationMiddleware)
        mock_provider_class.assert_called_once_with(
            logger_name="products_iam",
            cache_strategy="container"
        )
        mock_strategy_class.assert_called_once_with(mock_provider, "products_catalog")
        assert middleware.policy.caller_context == "products_catalog"
        assert middleware.policy.require_authentication is True

    @patch('src.contexts.shared_kernel.middleware.auth.authentication.UnifiedIAMProvider')
    @patch('src.contexts.shared_kernel.middleware.auth.authentication.AWSLambdaAuthenticationStrategy')
    def test_recipes_aws_auth_middleware(self, mock_strategy_class, mock_provider_class):
        """Test recipes AWS auth middleware factory."""
        mock_provider = MagicMock()
        mock_strategy = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_strategy_class.return_value = mock_strategy
        
        middleware = recipes_aws_auth_middleware()
        
        assert isinstance(middleware, AuthenticationMiddleware)
        mock_provider_class.assert_called_once_with(
            logger_name="recipes_iam",
            cache_strategy="container"
        )
        mock_strategy_class.assert_called_once_with(mock_provider, "recipes_catalog")
        assert middleware.policy.caller_context == "recipes_catalog"
        assert middleware.policy.require_authentication is True

    @patch('src.contexts.shared_kernel.middleware.auth.authentication.UnifiedIAMProvider')
    @patch('src.contexts.shared_kernel.middleware.auth.authentication.AWSLambdaAuthenticationStrategy')
    def test_client_onboarding_aws_auth_middleware(self, mock_strategy_class, mock_provider_class):
        """Test client onboarding AWS auth middleware factory."""
        mock_provider = MagicMock()
        mock_strategy = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_strategy_class.return_value = mock_strategy
        
        middleware = client_onboarding_aws_auth_middleware()
        
        assert isinstance(middleware, AuthenticationMiddleware)
        mock_provider_class.assert_called_once_with(
            logger_name="client_onboarding_iam",
            cache_strategy="container"
        )
        mock_strategy_class.assert_called_once_with(mock_provider, "client_onboarding")
        assert middleware.policy.caller_context == "client_onboarding"
        assert middleware.policy.require_authentication is True


# Error handling tests
class TestErrorHandling:
    """Test error handling and exception behavior."""

    def test_authentication_error_message(self):
        """Test AuthenticationError has correct message."""
        error = AuthenticationError(AUTHENTICATION_REQUIRED_MSG)
        assert str(error) == AUTHENTICATION_REQUIRED_MSG

    def test_authorization_error_message(self):
        """Test AuthorizationError has correct message."""
        error = AuthorizationError(INSUFFICIENT_PERMISSIONS_MSG)
        assert str(error) == INSUFFICIENT_PERMISSIONS_MSG

    @pytest.mark.anyio
    async def test_middleware_strategy_error_propagation(self, fake_strategy, fake_handler):
        """Test that strategy errors are propagated correctly."""
        # Setup
        fake_strategy.extract_auth_context.side_effect = ValueError("Strategy error")
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(ValueError, match="Strategy error"):
            await middleware(fake_handler, "event", "context")
        
        fake_strategy.cleanup.assert_called_once()

    @pytest.mark.anyio
    async def test_middleware_handler_error_propagation(self, fake_strategy, fake_handler):
        """Test that handler errors are propagated correctly."""
        # Setup
        auth_context = AuthContext(is_authenticated=True)
        fake_strategy.extract_auth_context.return_value = auth_context
        fake_strategy.get_request_data.return_value = ({"test": "data"}, "context")
        fake_handler.side_effect = RuntimeError("Handler error")
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # Execute & Verify
        with pytest.raises(RuntimeError, match="Handler error"):
            await middleware(fake_handler, "event", "context")
        
        fake_strategy.cleanup.assert_called_once()
