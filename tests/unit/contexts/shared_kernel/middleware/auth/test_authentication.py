"""Unit tests for authentication middleware.

Tests the authentication middleware behavior with fakes,
focusing on business logic and orchestration without I/O dependencies.
"""

import json
from typing import Any
from unittest.mock import MagicMock

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


# Fake implementations following testing principles
class FakeIAMProvider(UnifiedIAMProvider):
    """Fake IAM provider that implements the same interface as UnifiedIAMProvider."""
    
    def __init__(self, users: dict[str, dict[str, Any]] | None = None):
        """Initialize with a dictionary of user data."""
        super().__init__()
        self.users = users or {}
        self.clear_cache_called = False
    
    async def get_user(self, user_id: str, caller_context: str) -> dict[str, Any]:
        """Get user data from fake storage."""
        cache_key = f"{user_id}:{caller_context}"
        
        if cache_key in self._cache:
            self._cache_stats["hits"] += 1
            return self._cache[cache_key]
        
        self._cache_stats["misses"] += 1
        
        if user_id in self.users:
            user_data = self.users[user_id]
            response = {"statusCode": HTTP_OK, "body": user_data}
            self._cache[cache_key] = response
            return response
        else:
            response = {
                "statusCode": HTTP_INTERNAL_SERVER_ERROR,
                "body": json.dumps({"message": "User not found"})
            }
            self._cache[cache_key] = response
            return response
    
    def clear_cache(self):
        """Clear cache and track that it was called."""
        self.clear_cache_called = True
        super().clear_cache()
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            "cache_strategy": self.cache_strategy,
            "cache_hits": self._cache_stats["hits"],
            "cache_misses": self._cache_stats["misses"],
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 4),
            "cache_size": len(self._cache),
        }


class FakeAuthenticationStrategy(AuthenticationStrategy):
    """Fake authentication strategy that implements the same interface."""
    
    def __init__(self, auth_contexts: dict[str, AuthContext] | None = None):
        """Initialize with a dictionary of auth contexts by event key."""
        self.auth_contexts = auth_contexts or {}
        self.extract_called_with = []
        self.inject_called_with = []
        self.cleanup_called = False
    
    async def extract_auth_context(self, *args: Any, **kwargs: Any) -> AuthContext:
        """Extract auth context from fake storage."""
        event = args[0] if args else kwargs.get("event", {})
        context = args[1] if len(args) > 1 else kwargs.get("context")
        
        self.extract_called_with.append((event, context))
        
        # Use event as key to look up auth context
        event_key = str(event)
        return self.auth_contexts.get(event_key, AuthContext())
    
    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """Extract request data from arguments."""
        event = args[0] if args else kwargs.get("event", {})
        context = args[1] if len(args) > 1 else kwargs.get("context")
        return event, context
    
    def inject_auth_context(self, request_data: dict[str, Any], auth_context: AuthContext) -> None:
        """Inject auth context into request data."""
        self.inject_called_with.append((request_data, auth_context))
        request_data["_auth_context"] = auth_context
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.cleanup_called = True


class FakeHandler:
    """Fake endpoint handler for testing."""
    
    def __init__(self, responses: list[dict[str, Any]] | None = None):
        """Initialize with a list of responses to return."""
        self.responses = responses or [{"statusCode": 200, "body": "success"}]
        self.call_count = 0
        self.called_with = []
    
    async def __call__(self, *args, **kwargs) -> dict[str, Any]:
        """Handle the request."""
        self.called_with.append((args, kwargs))
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response


# Test fixtures
@fixture
def fake_iam_provider():
    """Fake IAM provider for testing."""
    return FakeIAMProvider()


@fixture
def fake_strategy():
    """Fake authentication strategy for testing."""
    return FakeAuthenticationStrategy()


@fixture
def fake_handler():
    """Fake endpoint handler for testing."""
    return FakeHandler()


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

    def test_has_required_role_none_allowed_roles(self):
        """Test has_required_role with None allowed_roles."""
        policy = AuthPolicy(allowed_roles=None)
        user_roles = ["admin", "user"]
        
        # Then: Should return True (no restrictions)
        assert policy.has_required_role(user_roles) is True

    def test_has_required_role_empty_allowed_roles(self):
        """Test has_required_role with empty allowed_roles."""
        policy = AuthPolicy(allowed_roles=[])
        user_roles = ["admin", "user"]
        
        # Then: Should return True (no restrictions)
        assert policy.has_required_role(user_roles) is True

    def test_has_required_role_case_sensitivity(self):
        """Test has_required_role with case-sensitive role comparison."""
        policy = AuthPolicy(allowed_roles=["Admin", "User"])
        user_roles = ["admin", "user"]  # Different case
        
        # Then: Should return False (case-sensitive comparison)
        assert policy.has_required_role(user_roles) is False

    def test_has_required_role_type_mismatch(self):
        """Test has_required_role with type mismatches."""
        policy = AuthPolicy(allowed_roles=["admin", "user"])
        user_roles = [123, "user"]  # Mixed types
        
        # Then: Should handle type mismatches gracefully
        assert policy.has_required_role(user_roles) is True  # "user" matches

    def test_has_required_role_none_user_roles(self):
        """Test has_required_role with None user_roles."""
        policy = AuthPolicy(allowed_roles=["admin"])
        
        # When/Then: Should handle None user_roles
        with pytest.raises((TypeError, AttributeError)):
            policy.has_required_role(None)  # type: ignore

    def test_has_required_role_empty_user_roles(self):
        """Test has_required_role with empty user_roles."""
        policy = AuthPolicy(allowed_roles=["admin"])
        user_roles = []
        
        # Then: Should return False (no matching roles)
        assert policy.has_required_role(user_roles) is False

    def test_auth_policy_none_allowed_roles_vs_empty_list(self):
        """Test AuthPolicy behavior with None vs empty list for allowed_roles."""
        # Given: Two policies with different None/empty list configurations
        policy_none = AuthPolicy(allowed_roles=None)
        policy_empty = AuthPolicy(allowed_roles=[])
        
        # When: Checking roles
        user_roles = ["admin"]
        result_none = policy_none.has_required_role(user_roles)
        result_empty = policy_empty.has_required_role(user_roles)
        
        # Then: Both should return True (no restrictions)
        assert result_none is True
        assert result_empty is True


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

    def test_auth_context_inconsistent_state_user_id_no_roles(self):
        """Test AuthContext with user_id but no roles."""
        # Given: AuthContext with user_id but no roles
        context = AuthContext(
            user_id="user123",
            user_roles=[],
            is_authenticated=False
        )
        
        # When/Then: Should handle inconsistent state
        assert context.user_id == "user123"
        assert context.user_roles == []
        assert context.is_authenticated is False

    def test_auth_context_inconsistent_state_roles_no_user_id(self):
        """Test AuthContext with roles but no user_id."""
        # Given: AuthContext with roles but no user_id
        context = AuthContext(
            user_id=None,
            user_roles=["admin"],
            is_authenticated=False
        )
        
        # When/Then: Should handle inconsistent state
        assert context.user_id is None
        assert context.user_roles == ["admin"]
        assert context.is_authenticated is False

    def test_auth_context_authenticated_no_user_object(self):
        """Test AuthContext with is_authenticated=True but no user_object."""
        # Given: AuthContext with is_authenticated=True but no user_object
        context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=True,
            user_object=None
        )
        
        # When/Then: Should handle state where user_object is None
        assert context.is_authenticated is True
        assert context.user_object is None
        assert context.has_permission("read") is False

    def test_auth_context_not_authenticated_with_user_object(self):
        """Test AuthContext with is_authenticated=False but user_object present."""
        # Given: AuthContext with is_authenticated=False but user_object present
        user_object = MagicMock()
        context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=False,
            user_object=user_object
        )
        
        # When/Then: Should handle state where is_authenticated is False
        assert context.is_authenticated is False
        assert context.user_object == user_object
        assert context.has_permission("read") is False

    def test_has_permission_with_none_permission(self):
        """Test has_permission with None permission string."""
        # Given: AuthContext with user object
        user_object = MagicMock()
        user_object.has_permission.return_value = True  # Mock returns truthy value
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        # When: Checking permission with None
        result = context.has_permission(None)  # type: ignore
        
        # Then: Should pass None to user_object and return its result
        assert result is True
        user_object.has_permission.assert_called_once_with(None)

    def test_has_permission_with_empty_permission(self):
        """Test has_permission with empty permission string."""
        # Given: AuthContext with user object
        user_object = MagicMock()
        user_object.has_permission.return_value = True  # Mock returns truthy value
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        # When: Checking permission with empty string
        result = context.has_permission("")
        
        # Then: Should call user_object.has_permission with empty string
        assert result is True
        user_object.has_permission.assert_called_once_with("")

    def test_has_permission_user_object_has_permission_returns_none(self):
        """Test has_permission when user_object.has_permission returns None."""
        # Given: AuthContext with user object that returns None
        user_object = MagicMock()
        user_object.has_permission.return_value = None
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        # When: Checking permission
        result = context.has_permission("read")
        
        # Then: Should return None (passes through user_object result)
        assert result is None

    def test_has_permission_user_object_raises_exception(self):
        """Test has_permission when user_object.has_permission raises exception."""
        # Given: AuthContext with user object that raises exception
        user_object = MagicMock()
        user_object.has_permission.side_effect = ValueError("Permission check failed")
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        # When/Then: Should raise the exception
        with pytest.raises(ValueError, match="Permission check failed"):
            context.has_permission("read")

    def test_has_permission_user_object_missing_method(self):
        """Test has_permission when user_object doesn't have has_permission method."""
        # Given: AuthContext with user object without has_permission method
        user_object = object()  # Plain object without has_permission method
        context = AuthContext(
            is_authenticated=True,
            user_object=user_object
        )
        
        # When/Then: Should raise AttributeError
        with pytest.raises(AttributeError):
            context.has_permission("read")

    def test_is_owner_or_has_permission_with_none_resource_owner_id(self):
        """Test is_owner_or_has_permission with None resource_owner_id."""
        # Given: AuthContext with user_id
        context = AuthContext(
            user_id="user123",
            is_authenticated=True
        )
        
        # When: Checking ownership with None resource_owner_id
        result = context.is_owner_or_has_permission(None, "read")  # type: ignore
        
        # Then: Should return False ("user123" != None)
        assert result is False

    def test_is_owner_or_has_permission_with_empty_resource_owner_id(self):
        """Test is_owner_or_has_permission with empty resource_owner_id."""
        # Given: AuthContext with user_id
        context = AuthContext(
            user_id="user123",
            is_authenticated=True
        )
        
        # When: Checking ownership with empty resource_owner_id
        result = context.is_owner_or_has_permission("", "read")
        
        # Then: Should return False ("" != "user123")
        assert result is False


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
    async def test_get_user_success(self):
        """Test successful user retrieval."""
        # Given: A fake IAM provider with user data
        user_data = {"id": "user123", "roles": ["admin"]}
        provider = FakeIAMProvider(users={"user123": user_data})
        
        # When: Getting user data
        result = await provider.get_user("user123", "products_catalog")
        
        # Then: Should return success response
        assert result["statusCode"] == HTTP_OK
        assert result["body"] == user_data

    @pytest.mark.anyio
    async def test_get_user_error(self):
        """Test user retrieval with error response."""
        # Given: A fake IAM provider without the user
        provider = FakeIAMProvider()
        
        # When: Getting non-existent user data
        result = await provider.get_user("user123", "products_catalog")
        
        # Then: Should return error response
        assert result["statusCode"] == HTTP_INTERNAL_SERVER_ERROR
        assert "User not found" in result["body"]

    @pytest.mark.anyio
    async def test_get_user_caching(self):
        """Test that user data is cached correctly."""
        # Given: A fake IAM provider with user data
        user_data = {"id": "user123", "roles": ["admin"]}
        provider = FakeIAMProvider(users={"user123": user_data})
        
        # When: Getting the same user twice
        result1 = await provider.get_user("user123", "products_catalog")
        result2 = await provider.get_user("user123", "products_catalog")
        
        # Then: Should return same data and cache should be used
        assert result1 == result2
        stats = provider.get_cache_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1

    def test_clear_cache_request_strategy(self):
        """Test cache clearing with request strategy."""
        # Given: A provider with cached data
        provider = FakeIAMProvider()
        provider._cache = {"user123:products_catalog": {"id": "user123"}}
        
        # When: Clearing cache
        provider.clear_cache()
        
        # Then: Cache should be cleared and method should be tracked
        assert provider._cache == {}
        assert provider.clear_cache_called is True

    def test_clear_cache_container_strategy(self):
        """Test cache clearing with container strategy."""
        # Given: A provider with container strategy and cached data
        provider = FakeIAMProvider()
        provider.cache_strategy = "container"
        provider._cache = {"user123:products_catalog": {"id": "user123"}}
        
        # When: Clearing cache
        provider.clear_cache()
        
        # Then: Cache should not be cleared but method should be tracked
        assert provider._cache == {"user123:products_catalog": {"id": "user123"}}
        assert provider.clear_cache_called is True

    def test_get_cache_stats_empty(self):
        """Test cache statistics with no requests."""
        # Given: A fresh provider
        provider = FakeIAMProvider()
        
        # When: Getting cache stats
        stats = provider.get_cache_stats()
        
        # Then: Should show no activity
        assert stats["cache_strategy"] == "request"
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["cache_size"] == 0

    def test_get_cache_stats_with_data(self):
        """Test cache statistics with some requests."""
        # Given: A provider with some cache activity
        provider = FakeIAMProvider()
        provider._cache_stats = {"hits": 8, "misses": 2}
        provider._cache = {"user1:context1": {}, "user2:context2": {}}
        
        # When: Getting cache stats
        stats = provider.get_cache_stats()
        
        # Then: Should show correct statistics
        assert stats["cache_strategy"] == "request"
        assert stats["cache_hits"] == 8
        assert stats["cache_misses"] == 2
        assert stats["total_requests"] == 10
        assert stats["hit_rate"] == 0.8
        assert stats["cache_size"] == 2


# AWSLambdaAuthenticationStrategy tests
class TestAWSLambdaAuthenticationStrategy:
    """Test AWS Lambda authentication strategy behavior."""

    @pytest.mark.anyio
    async def test_extract_auth_context_valid_token(self, sample_event, sample_context):
        """Test extracting auth context with valid token."""
        # Given: A fake IAM provider with user data and a strategy
        user_data = {"id": "user123", "roles": ["admin"]}
        fake_iam_provider = FakeIAMProvider(users={"user123": user_data})
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(sample_event, sample_context)
        
        # Then: Should return authenticated context with user data
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
    async def test_extract_auth_context_invalid_token(self):
        """Test extracting auth context with invalid token."""
        # Given: A strategy with empty claims
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {"claims": {}}}}
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_missing_token(self):
        """Test extracting auth context with missing token."""
        # Given: A strategy with missing authorizer
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {}}
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_missing_request_context(self):
        """Test extracting auth context with missing requestContext."""
        # Given: A strategy with missing requestContext
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {}  # No requestContext
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When/Then: Should raise error for missing requestContext
        with pytest.raises(ValueError, match="Event and context are required"):
            await strategy.extract_auth_context(event, context)

    @pytest.mark.anyio
    async def test_extract_auth_context_missing_authorizer(self):
        """Test extracting auth context with missing authorizer."""
        # Given: A strategy with missing authorizer
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {}}  # No authorizer
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_missing_claims(self):
        """Test extracting auth context with missing claims."""
        # Given: A strategy with missing claims
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {}}}  # No claims
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_none_claims(self):
        """Test extracting auth context with None claims."""
        # Given: A strategy with None claims
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {"claims": None}}}
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When/Then: Should raise error for None claims
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'get'"):
            await strategy.extract_auth_context(event, context)

    @pytest.mark.anyio
    async def test_extract_auth_context_empty_user_id(self):
        """Test extracting auth context with empty user_id."""
        # Given: A strategy with empty user_id
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {"claims": {"sub": ""}}}}
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id == ""
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_none_user_id(self):
        """Test extracting auth context with None user_id."""
        # Given: A strategy with None user_id
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {"claims": {"sub": None}}}}
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id is None
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    @pytest.mark.anyio
    async def test_extract_auth_context_non_string_user_id(self):
        """Test extracting auth context with non-string user_id."""
        # Given: A strategy with non-string user_id
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        event = {"requestContext": {"authorizer": {"claims": {"sub": 123}}}}
        context = type("Context", (), {"function_name": "test", "request_id": "req-123"})()
        
        # When: Extracting auth context
        auth_context = await strategy.extract_auth_context(event, context)
        
        # Then: Should return unauthenticated context
        assert auth_context.user_id == 123
        assert auth_context.user_roles == []
        assert auth_context.is_authenticated is False

    def test_get_request_data_positional_args(self, sample_event, sample_context):
        """Test getting request data from positional arguments."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When: Getting request data with positional args
        event, context = strategy.get_request_data(sample_event, sample_context)
        
        # Then: Should return the same data
        assert event == sample_event
        assert context == sample_context

    def test_get_request_data_keyword_args(self, sample_event, sample_context):
        """Test getting request data from keyword arguments."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When: Getting request data with keyword args
        event, context = strategy.get_request_data(event=sample_event, context=sample_context)
        
        # Then: Should return the same data
        assert event == sample_event
        assert context == sample_context

    def test_get_request_data_missing_args(self):
        """Test getting request data with missing arguments."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When/Then: Should raise error for missing args
        with pytest.raises(IndexError):
            strategy.get_request_data()

    def test_get_request_data_none_event(self):
        """Test getting request data with None event."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When/Then: Should raise error for None event
        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data(None, "context")

    def test_get_request_data_none_context(self):
        """Test getting request data with None context."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When/Then: Should raise error for None context
        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data({"test": "event"}, None)

    def test_get_request_data_both_none(self):
        """Test getting request data with both None event and context."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When/Then: Should raise error for both None
        with pytest.raises(ValueError, match="Event and context are required"):
            strategy.get_request_data(None, None)

    def test_get_request_data_non_dict_event(self):
        """Test getting request data with non-dict event."""
        # Given: A strategy
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When: Getting request data with string event
        event, context = strategy.get_request_data("not_a_dict", "context")
        
        # Then: Should return the string as event (strategy doesn't validate type)
        assert event == "not_a_dict"
        assert context == "context"

    def test_inject_auth_context(self, sample_event):
        """Test injecting auth context into request data."""
        # Given: A strategy and auth context
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        auth_context = AuthContext(user_id="user123", is_authenticated=True)
        
        # When: Injecting auth context
        strategy.inject_auth_context(sample_event, auth_context)
        
        # Then: Auth context should be in the event
        assert sample_event["_auth_context"] == auth_context

    def test_extract_user_roles_custom_roles(self):
        """Test extracting user roles from custom claims."""
        # Given: A strategy and claims with custom roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": "admin,user,moderator"}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return all roles without duplicates
        assert set(roles) == {"admin", "user", "moderator"}
        assert len(roles) == 3

    def test_extract_user_roles_cognito_groups(self):
        """Test extracting user roles from cognito groups."""
        # Given: A strategy and claims with cognito groups
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"cognito:groups": ["admin", "user"]}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return all roles
        assert set(roles) == {"admin", "user"}
        assert len(roles) == 2

    def test_extract_user_roles_scope(self):
        """Test extracting user roles from OAuth scope."""
        # Given: A strategy and claims with OAuth scope
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"scope": "read write admin"}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return all scopes as roles
        assert set(roles) == {"read", "write", "admin"}
        assert len(roles) == 3

    def test_extract_user_roles_duplicates(self):
        """Test extracting user roles removes duplicates."""
        # Given: A strategy and claims with overlapping roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {
            "custom:roles": "admin,user",
            "cognito:groups": ["admin", "moderator"]
        }
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return unique roles only
        assert set(roles) == {"admin", "user", "moderator"}

    def test_extract_user_roles_empty_custom_roles(self):
        """Test extracting user roles with empty custom roles claim."""
        # Given: A strategy and claims with empty custom roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": ""}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_whitespace_custom_roles(self):
        """Test extracting user roles with whitespace-only custom roles claim."""
        # Given: A strategy and claims with whitespace-only custom roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": "   "}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_malformed_custom_roles(self):
        """Test extracting user roles with malformed custom roles claim."""
        # Given: A strategy and claims with malformed custom roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": "admin,user,moderator,admin,user"}  # Duplicates in same source
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return unique roles only
        assert set(roles) == {"admin", "user", "moderator"}

    def test_extract_user_roles_non_string_custom_roles(self):
        """Test extracting user roles with non-string custom roles claim."""
        # Given: A strategy and claims with non-string custom roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": 123}  # Number instead of string
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_empty_cognito_groups(self):
        """Test extracting user roles with empty cognito groups."""
        # Given: A strategy and claims with empty cognito groups
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"cognito:groups": []}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_non_array_cognito_groups(self):
        """Test extracting user roles with non-array cognito groups."""
        # Given: A strategy and claims with non-array cognito groups
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"cognito:groups": "admin,user"}  # String instead of array
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should parse as comma-separated string
        assert set(roles) == {"admin", "user"}

    def test_extract_user_roles_non_string_cognito_groups(self):
        """Test extracting user roles with non-string elements in cognito groups."""
        # Given: A strategy and claims with non-string elements in cognito groups
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"cognito:groups": ["admin", 123, "user"]}  # Mixed types
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should include all elements (strategy doesn't filter by type)
        assert set(roles) == {"admin", 123, "user"}

    def test_extract_user_roles_empty_scope(self):
        """Test extracting user roles with empty scope claim."""
        # Given: A strategy and claims with empty scope
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"scope": ""}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_whitespace_scope(self):
        """Test extracting user roles with whitespace-only scope claim."""
        # Given: A strategy and claims with whitespace-only scope
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"scope": "   "}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_non_string_scope(self):
        """Test extracting user roles with non-string scope claim."""
        # Given: A strategy and claims with non-string scope
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"scope": 123}  # Number instead of string
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return empty list
        assert roles == []

    def test_extract_user_roles_special_characters(self):
        """Test extracting user roles with special characters."""
        # Given: A strategy and claims with special characters in roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": "admin@domain,user-role,moderator_role"}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should return all roles including special characters
        assert set(roles) == {"admin@domain", "user-role", "moderator_role"}

    def test_extract_user_roles_case_sensitivity(self):
        """Test extracting user roles preserves case sensitivity."""
        # Given: A strategy and claims with mixed case roles
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        claims = {"custom:roles": "Admin,USER,moderator"}
        
        # When: Extracting user roles
        roles = strategy._extract_user_roles(claims)
        
        # Then: Should preserve case
        assert set(roles) == {"Admin", "USER", "moderator"}

    @pytest.mark.anyio
    async def test_cleanup(self):
        """Test cleanup method."""
        # Given: A strategy with a fake IAM provider
        fake_iam_provider = FakeIAMProvider()
        strategy = AWSLambdaAuthenticationStrategy(fake_iam_provider, "products_catalog")
        
        # When: Cleaning up
        await strategy.cleanup()
        
        # Then: IAM provider cache should be cleared
        assert fake_iam_provider.clear_cache_called is True


# AuthenticationMiddleware tests
class TestAuthenticationMiddleware:
    """Test AuthenticationMiddleware behavior and orchestration."""

    @pytest.mark.anyio
    async def test_authentication_middleware_valid_token(self):
        """Test authentication middleware with valid token."""
        # Given: A fake strategy that returns authenticated context and a handler
        auth_context = AuthContext(
            user_id="user123",
            user_roles=["admin"],
            is_authenticated=True
        )
        fake_strategy = FakeAuthenticationStrategy({str({"test": "event"}): auth_context})
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True, allowed_roles=["admin"])
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When: Executing middleware
        result = await middleware(fake_handler, {"test": "event"}, "context")
        
        # Then: Should return success and track interactions
        assert result == {"statusCode": 200, "body": "success"}
        assert len(fake_strategy.extract_called_with) == 1
        assert len(fake_strategy.inject_called_with) == 1
        assert fake_strategy.cleanup_called is True
        assert fake_handler.call_count == 1

    @pytest.mark.anyio
    async def test_authentication_middleware_invalid_token(self):
        """Test authentication middleware with invalid token."""
        # Given: A fake strategy that returns unauthenticated context
        fake_strategy = FakeAuthenticationStrategy()
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should raise authentication error
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, {"test": "event"}, "context")
        
        # And: Should track interactions and cleanup
        assert len(fake_strategy.extract_called_with) == 1
        assert fake_strategy.cleanup_called is True

    @pytest.mark.anyio
    async def test_authentication_middleware_expired_token(self):
        """Test authentication middleware with expired token."""
        # Given: A fake strategy that returns expired token context
        auth_context = AuthContext(
            user_id="user123",
            is_authenticated=False  # Expired token results in not authenticated
        )
        fake_strategy = FakeAuthenticationStrategy({str({"test": "event"}): auth_context})
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should raise authentication error
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, {"test": "event"}, "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_missing_token(self):
        """Test authentication middleware with missing token."""
        # Given: A fake strategy that returns unauthenticated context
        fake_strategy = FakeAuthenticationStrategy()
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should raise authentication error
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, {"test": "event"}, "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_insufficient_permissions(self):
        """Test authentication middleware with insufficient permissions."""
        # Given: A fake strategy that returns authenticated but unauthorized context
        auth_context = AuthContext(
            user_id="user123",
            user_roles=["user"],  # User doesn't have admin role
            is_authenticated=True
        )
        fake_strategy = FakeAuthenticationStrategy({str({"test": "event"}): auth_context})
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True, allowed_roles=["admin"])
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should raise authorization error
        with pytest.raises(AuthorizationError, match=INSUFFICIENT_PERMISSIONS_MSG):
            await middleware(fake_handler, {"test": "event"}, "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_no_auth_required(self):
        """Test authentication middleware when authentication is not required."""
        # Given: A fake strategy that returns unauthenticated context but auth not required
        fake_strategy = FakeAuthenticationStrategy()
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=False)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When: Executing middleware
        result = await middleware(fake_handler, {"test": "event"}, "context")
        
        # Then: Should return success and track interactions
        assert result == {"statusCode": 200, "body": "success"}
        assert len(fake_strategy.extract_called_with) == 1
        assert len(fake_strategy.inject_called_with) == 1

    @pytest.mark.anyio
    async def test_authentication_middleware_cleanup_on_error(self):
        """Test that cleanup is called even when authentication fails."""
        # Given: A fake strategy that returns unauthenticated context
        fake_strategy = FakeAuthenticationStrategy()
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should raise error but still cleanup
        with pytest.raises(AuthenticationError):
            await middleware(fake_handler, {"test": "event"}, "context")
        
        assert fake_strategy.cleanup_called is True

    def test_get_auth_context(self):
        """Test getting auth context from request data."""
        # Given: A middleware and request data with auth context
        fake_strategy = FakeAuthenticationStrategy()
        middleware = AuthenticationMiddleware(strategy=fake_strategy)
        auth_context = AuthContext(user_id="user123")
        request_data = {"_auth_context": auth_context}
        
        # When: Getting auth context
        result = middleware.get_auth_context(request_data)
        
        # Then: Should return the auth context
        assert result == auth_context

    def test_get_auth_context_not_found(self):
        """Test getting auth context when not present."""
        # Given: A middleware and request data without auth context
        fake_strategy = FakeAuthenticationStrategy()
        middleware = AuthenticationMiddleware(strategy=fake_strategy)
        request_data = {}
        
        # When: Getting auth context
        result = middleware.get_auth_context(request_data)
        
        # Then: Should return None
        assert result is None

    @pytest.mark.anyio
    async def test_authentication_middleware_none_policy(self):
        """Test authentication middleware with None policy."""
        # Given: A middleware with None policy (should use default)
        fake_strategy = FakeAuthenticationStrategy()
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=None)
        fake_handler = FakeHandler()
        
        # When/Then: Should use default policy (require_authentication=True)
        with pytest.raises(AuthenticationError, match=AUTHENTICATION_REQUIRED_MSG):
            await middleware(fake_handler, {"test": "event"}, "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_cleanup_method_missing(self):
        """Test authentication middleware when strategy has no cleanup method."""
        # Given: A strategy without cleanup method
        class NoCleanupStrategy(FakeAuthenticationStrategy):
            def __init__(self):
                super().__init__()
                self.cleanup_called = False
            
            # No cleanup method defined
        
        fake_strategy = NoCleanupStrategy()
        auth_context = AuthContext(is_authenticated=True)
        fake_strategy.auth_contexts = {str({"test": "event"}): auth_context}
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When: Executing middleware
        result = await middleware(fake_handler, {"test": "event"}, "context")
        
        # Then: Should work without cleanup method
        assert result == {"statusCode": 200, "body": "success"}

    @pytest.mark.anyio
    async def test_authentication_middleware_cleanup_method_not_async(self):
        """Test authentication middleware when strategy cleanup method is not async."""
        # Given: A strategy with non-async cleanup method
        class SyncCleanupStrategy(FakeAuthenticationStrategy):
            def __init__(self):
                super().__init__()
                self.cleanup_called = False
            
            def cleanup(self):  # Not async
                self.cleanup_called = True
        
        fake_strategy = SyncCleanupStrategy()
        auth_context = AuthContext(is_authenticated=True)
        fake_strategy.auth_contexts = {str({"test": "event"}): auth_context}
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should raise error when trying to await sync method
        with pytest.raises(TypeError, match="object NoneType can't be used in 'await' expression"):
            await middleware(fake_handler, {"test": "event"}, "context")

    @pytest.mark.anyio
    async def test_authentication_middleware_cleanup_raises_exception(self):
        """Test authentication middleware when strategy cleanup raises exception."""
        # Given: A strategy with cleanup that raises exception
        class ErrorCleanupStrategy(FakeAuthenticationStrategy):
            def __init__(self):
                super().__init__()
                self.cleanup_called = False
            
            async def cleanup(self):
                self.cleanup_called = True
                raise ValueError("Cleanup error")
        
        fake_strategy = ErrorCleanupStrategy()
        auth_context = AuthContext(is_authenticated=True)
        fake_strategy.auth_contexts = {str({"test": "event"}): auth_context}
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should propagate cleanup error
        with pytest.raises(ValueError, match="Cleanup error"):
            await middleware(fake_handler, {"test": "event"}, "context")
        
        assert fake_strategy.cleanup_called is True


# Factory function tests
class TestFactoryFunctions:
    """Test factory functions for creating authentication middleware."""

    def test_create_auth_middleware_defaults(self):
        """Test create_auth_middleware with default values."""
        # Given: A fake strategy
        fake_strategy = FakeAuthenticationStrategy()
        
        # When: Creating middleware with defaults
        middleware = create_auth_middleware(strategy=fake_strategy)
        
        # Then: Should create middleware with default policy
        assert isinstance(middleware, AuthenticationMiddleware)
        assert middleware.strategy == fake_strategy
        assert middleware.policy.require_authentication is True
        assert middleware.policy.allowed_roles == []
        assert middleware.policy.caller_context is None

    def test_create_auth_middleware_custom_values(self):
        """Test create_auth_middleware with custom values."""
        # Given: A fake strategy
        fake_strategy = FakeAuthenticationStrategy()
        
        # When: Creating middleware with custom values
        middleware = create_auth_middleware(
            strategy=fake_strategy,
            require_authentication=False,
            allowed_roles=["admin"],
            caller_context="test_context",
            name="test_middleware",
            timeout=30.0
        )
        
        # Then: Should create middleware with custom policy
        assert isinstance(middleware, AuthenticationMiddleware)
        assert middleware.strategy == fake_strategy
        assert middleware.policy.require_authentication is False
        assert middleware.policy.allowed_roles == ["admin"]
        assert middleware.policy.caller_context == "test_context"
        assert middleware.name == "test_middleware"
        assert middleware.timeout == 30.0

    def test_products_aws_auth_middleware(self):
        """Test products AWS auth middleware factory."""
        # When: Creating products auth middleware
        middleware = products_aws_auth_middleware()
        
        # Then: Should create middleware with correct configuration
        assert isinstance(middleware, AuthenticationMiddleware)
        assert isinstance(middleware.strategy, AWSLambdaAuthenticationStrategy)
        assert isinstance(middleware.strategy.iam_provider, UnifiedIAMProvider)
        assert middleware.strategy.iam_provider.cache_strategy == "container"
        assert middleware.strategy.caller_context == "products_catalog"
        assert middleware.policy.caller_context == "products_catalog"
        assert middleware.policy.require_authentication is True

    def test_recipes_aws_auth_middleware(self):
        """Test recipes AWS auth middleware factory."""
        # When: Creating recipes auth middleware
        middleware = recipes_aws_auth_middleware()
        
        # Then: Should create middleware with correct configuration
        assert isinstance(middleware, AuthenticationMiddleware)
        assert isinstance(middleware.strategy, AWSLambdaAuthenticationStrategy)
        assert isinstance(middleware.strategy.iam_provider, UnifiedIAMProvider)
        assert middleware.strategy.iam_provider.cache_strategy == "container"
        assert middleware.strategy.caller_context == "recipes_catalog"
        assert middleware.policy.caller_context == "recipes_catalog"
        assert middleware.policy.require_authentication is True

    def test_client_onboarding_aws_auth_middleware(self):
        """Test client onboarding AWS auth middleware factory."""
        # When: Creating client onboarding auth middleware
        middleware = client_onboarding_aws_auth_middleware()
        
        # Then: Should create middleware with correct configuration
        assert isinstance(middleware, AuthenticationMiddleware)
        assert isinstance(middleware.strategy, AWSLambdaAuthenticationStrategy)
        assert isinstance(middleware.strategy.iam_provider, UnifiedIAMProvider)
        assert middleware.strategy.iam_provider.cache_strategy == "container"
        assert middleware.strategy.caller_context == "client_onboarding"
        assert middleware.policy.caller_context == "client_onboarding"
        assert middleware.policy.require_authentication is True


# Error handling tests
class TestErrorHandling:
    """Test error handling and exception behavior."""

    def test_authentication_error_message(self):
        """Test AuthenticationError has correct message."""
        # Given/When: Creating an authentication error
        error = AuthenticationError(AUTHENTICATION_REQUIRED_MSG)
        
        # Then: Should have correct message
        assert str(error) == AUTHENTICATION_REQUIRED_MSG

    def test_authorization_error_message(self):
        """Test AuthorizationError has correct message."""
        # Given/When: Creating an authorization error
        error = AuthorizationError(INSUFFICIENT_PERMISSIONS_MSG)
        
        # Then: Should have correct message
        assert str(error) == INSUFFICIENT_PERMISSIONS_MSG

    @pytest.mark.anyio
    async def test_middleware_strategy_error_propagation(self):
        """Test that strategy errors are propagated correctly."""
        # Given: A fake strategy that raises an error
        class ErrorStrategy(FakeAuthenticationStrategy):
            async def extract_auth_context(self, *args, **kwargs):
                raise ValueError("Strategy error")
        
        fake_strategy = ErrorStrategy()
        fake_handler = FakeHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should propagate the error and cleanup
        with pytest.raises(ValueError, match="Strategy error"):
            await middleware(fake_handler, {"test": "event"}, "context")
        
        assert fake_strategy.cleanup_called is True

    @pytest.mark.anyio
    async def test_middleware_handler_error_propagation(self):
        """Test that handler errors are propagated correctly."""
        # Given: A fake strategy that works and a handler that raises an error
        auth_context = AuthContext(is_authenticated=True)
        fake_strategy = FakeAuthenticationStrategy({str({"test": "event"}): auth_context})
        
        class ErrorHandler(FakeHandler):
            async def __call__(self, *args, **kwargs):
                raise RuntimeError("Handler error")
        
        fake_handler = ErrorHandler()
        
        policy = AuthPolicy(require_authentication=True)
        middleware = AuthenticationMiddleware(strategy=fake_strategy, policy=policy)
        
        # When/Then: Should propagate the error and cleanup
        with pytest.raises(RuntimeError, match="Handler error"):
            await middleware(fake_handler, {"test": "event"}, "context")
        
        assert fake_strategy.cleanup_called is True
