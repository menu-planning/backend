"""Unified authentication middleware for the shared kernel.

This module provides a generic, composable authentication middleware that
inherits from BaseMiddleware and integrates with the unified middleware system.
It uses composition to support different authentication strategies
(AWS Lambda, FastAPI, etc.).
"""

import json
from abc import ABC, abstractmethod
from typing import Any

import src.contexts.iam.core.internal_endpoints.get as iam_internal_api
from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.logging.logger import StructlogFactory, correlation_id_ctx

logger = StructlogFactory.get_logger(__name__)

try:
    from src.contexts.products_catalog.core.adapters.api_schemas.value_objects.api_user import (
        ApiUser as ProductsApiUser,
    )
except ImportError:
    ProductsApiUser = None

try:
    from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import (
        ApiUser as RecipesApiUser,
    )
except ImportError:
    RecipesApiUser = None

try:
    from src.contexts.client_onboarding.core.adapters.api_schemas.value_objects.api_user import (
        ApiUser as ClientOnboardingApiUser,
    )
except ImportError:
    ClientOnboardingApiUser = None

# Error message constants
AUTHENTICATION_REQUIRED_MSG = "Authentication required"
INSUFFICIENT_PERMISSIONS_MSG = "Insufficient permissions"

# HTTP status codes
HTTP_OK = 200
HTTP_INTERNAL_SERVER_ERROR = 500


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthorizationError(Exception):
    """Raised when authorization fails."""


class AuthPolicy:
    """Simple authentication policy configuration.

    Following the KISS principle, this provides a straightforward way to
    configure authentication requirements without complex rule engines.

    Attributes:
        require_authentication: Whether authentication is required.
        allowed_roles: List of allowed roles (None = any authenticated user).
        caller_context: The calling context for IAM integration.

    Notes:
        Immutable after creation. Equality by value (require_authentication, allowed_roles, caller_context).
    """

    def __init__(
        self,
        *,
        require_authentication: bool = True,
        allowed_roles: list[str] | None = None,
        caller_context: str | None = None,
    ):
        """Initialize authentication policy.

        Args:
            require_authentication: Whether authentication is required.
            allowed_roles: List of allowed roles (None = any authenticated user).
            caller_context: The calling context for IAM integration.
        """
        self.require_authentication = require_authentication
        self.allowed_roles = allowed_roles or []
        self.caller_context = caller_context

    def is_authenticated_required(self) -> bool:
        """Check if authentication is required."""
        return self.require_authentication

    def has_required_role(self, user_roles: list[str]) -> bool:
        """Check if user has required role."""
        if not self.allowed_roles:
            return True  # No role restrictions
        return any(role in user_roles for role in self.allowed_roles)


class UnifiedIAMProvider:
    """Unified IAMProvider that consolidates all context-specific implementations.

    Features:
    - Single source of truth for IAM integration
    - Configurable caching strategies to reduce IAM calls
    - Consistent error handling and logging
    - Context-aware user data filtering
    - Backward compatibility with existing patterns
    - Cache performance monitoring

    Attributes:
        structured_logger: Logger instance for IAM operations.
        _cache: Cache for user data (strategy-dependent scope).
        cache_strategy: Caching strategy ("request" or "container").
        _cache_stats: Cache performance statistics.

    Notes:
        Thread-safe: No (uses strategy-dependent cache).
        Caching: Configurable scope to reduce IAM calls.
        FastAPI: Requires request-scoped instances to avoid race conditions.
    """

    def __init__(
        self, logger_name: str = "iam_provider", cache_strategy: str = "request"
    ):
        """Initialize UnifiedIAMProvider.

        Args:
            logger_name: Name for the structured logger.
            cache_strategy: Caching strategy ("request" or "container").
                - "request": Cache cleared after each request (default, current behavior)
                - "container": Cache persists across requests (optimized for Lambda containers)
        """
        # Ensure structlog is configured
        StructlogFactory.configure()
        self.structured_logger = StructlogFactory.get_logger(logger_name)
        self.cache_strategy = cache_strategy
        self._cache = {}  # Strategy-dependent cache
        self._cache_stats = {"hits": 0, "misses": 0}

    async def get_user(self, user_id: str, caller_context: str) -> dict[str, Any]:
        """Get user data from IAM with caching and error handling.

        Args:
            user_id: The user ID to fetch.
            caller_context: The calling context
                (e.g., "products_catalog", "recipes_catalog").

        Returns:
            Dictionary with statusCode and body (SeedUser object on success).

        Raises:
            AuthenticationError: When IAM call fails.

        Notes:
            Uses request-scoped caching to reduce IAM calls.
            Validates caller_context against supported contexts.
        """
        # Validate caller_context first
        supported_contexts = [
            "products_catalog",
            "recipes_catalog",
            "client_onboarding",
        ]
        if caller_context not in supported_contexts:
            error_message = (
                f"Unsupported caller context: {caller_context}. "
                f"Supported contexts: {', '.join(supported_contexts)}"
            )
            correlation_id = correlation_id_ctx.get() or "unknown"
            self.structured_logger.warning(
                "Unsupported caller context requested",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                supported_contexts=supported_contexts,
            )
            return {
                "statusCode": HTTP_INTERNAL_SERVER_ERROR,
                "body": json.dumps({"message": error_message}),
            }

        # Check cache first (strategy-dependent scope)
        cache_key = f"{user_id}:{caller_context}"
        correlation_id = correlation_id_ctx.get() or "unknown"

        if cache_key in self._cache:
            self._cache_stats["hits"] += 1
            self.structured_logger.debug(
                "IAM user data retrieved from cache",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                cache_strategy=self.cache_strategy,
                cache_hit_rate=self._get_cache_hit_rate(),
            )
            return self._cache[cache_key]

        try:
            self._cache_stats["misses"] += 1
            self.structured_logger.debug(
                "Fetching user data from IAM",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                cache_strategy=self.cache_strategy,
                cache_hit_rate=self._get_cache_hit_rate(),
            )

            # Call internal IAM endpoint
            response = await iam_internal_api.get(
                id=user_id, caller_context=caller_context
            )

            if response.get("statusCode") != HTTP_OK:
                self.structured_logger.warning(
                    "IAM provider returned error",
                    correlation_id=correlation_id,
                    user_id_suffix=(
                        user_id[-4:] if len(user_id) >= 4 else user_id
                    ),  # Last 4 chars for debugging
                    caller_context=caller_context,
                    status_code=response.get("statusCode"),
                    response_body_type=type(
                        response.get("body")
                    ).__name__,  # Type only, not content
                    response_body_length=(
                        len(str(response.get("body", "")))
                        if response.get("body")
                        else 0
                    ),
                )
                # Cache error response to avoid repeated failed calls
                self._cache[cache_key] = response
                return response

            # Convert via appropriate context-specific IAMUser schema
            if caller_context == "products_catalog":
                api_user_class = ProductsApiUser
            elif caller_context == "recipes_catalog":
                api_user_class = RecipesApiUser
            elif caller_context == "client_onboarding":
                api_user_class = ClientOnboardingApiUser

            assert api_user_class is not None
            assert isinstance(response["body"], str)
            iam_user = api_user_class.model_validate_json(response["body"])
            seed_user = iam_user.to_domain()

            # Create successful response
            success_response = {"statusCode": HTTP_OK, "body": seed_user}

            # Cache successful response
            self._cache[cache_key] = success_response

            self.structured_logger.info(
                "User authenticated successfully",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                user_roles_count=len(iam_user.roles),
            )
        except Exception as e:
            self.structured_logger.error(
                "IAM provider call failed",
                correlation_id=correlation_id,
                exc_info=True,
                user_id=user_id,
                caller_context=caller_context,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )
            return {
                "statusCode": HTTP_INTERNAL_SERVER_ERROR,
                "body": json.dumps({"message": "Authentication service error"}),
            }
        else:
            return success_response

    def clear_cache(self):
        """Clear cache based on strategy.

        - "request" strategy: Always clears cache (current behavior)
        - "container" strategy: Does not clear cache (optimized for Lambda containers)
        """
        if self.cache_strategy == "request":
            self._cache.clear()
        elif self.cache_strategy == "container":
            # Don't clear cache - let it persist across requests
            pass
        else:
            # Default to clearing for unknown strategies
            self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache hit/miss statistics and performance metrics.
        """
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            self._cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
        )

        return {
            "cache_strategy": self.cache_strategy,
            "cache_hits": self._cache_stats["hits"],
            "cache_misses": self._cache_stats["misses"],
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 4),
            "cache_size": len(self._cache),
        }

    def _get_cache_hit_rate(self) -> float:
        """Get current cache hit rate as a percentage."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        return round((self._cache_stats["hits"] / total_requests) * 100, 2)


class AuthContext:
    """
    Authentication context for the current request.

    Simple container for user authentication data that follows
    the established patterns in the codebase.
    """

    def __init__(
        self,
        *,
        user_id: str | None = None,
        user_roles: list[str] | None = None,
        is_authenticated: bool = False,
        metadata: dict[str, Any] | None = None,
        user_object: Any = None,
        caller_context: str | None = None,
    ):
        """
        Initialize authentication context.

        Args:
            user_id: Unique identifier for the user
            user_roles: List of roles assigned to the user
            is_authenticated: Whether the user is authenticated
            metadata: Additional authentication metadata
            user_object: The full user object from IAM (SeedUser)
            caller_context: The calling context for this authentication
        """
        self.user_id = user_id
        self.user_roles = user_roles or []
        self.is_authenticated = is_authenticated
        self.metadata = metadata or {}
        self.user_object = user_object
        self.caller_context = caller_context

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.user_roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.user_roles for role in roles)

    def has_permission(self, permission: str, context: str | None = None) -> bool:
        """Check if user has specific permission, optionally in a specific context."""
        if not self.is_authenticated or not self.user_object:
            return False

        # For IAM context, use context-specific permission checking
        if context:
            return self.user_object.has_permission(context, permission)
        return self.user_object.has_permission(permission)

    def is_owner_or_has_permission(
        self, resource_owner_id: str, permission: str
    ) -> bool:
        """Check if user is the resource owner OR has the specified permission."""
        if not self.is_authenticated:
            return False

        return self.user_id == resource_owner_id or self.has_permission(permission)

    @property
    def user(self):
        """Get SeedUser object."""
        return self.user_object

    def __repr__(self) -> str:
        """String representation of auth context."""
        roles_str = f", roles={self.user_roles}" if self.user_roles else ""
        return (
            f"AuthContext(user_id={self.user_id}, "
            f"authenticated={self.is_authenticated}{roles_str})"
        )


class AuthenticationStrategy(ABC):
    """
    Abstract base class for authentication strategies.

    This interface defines how different platforms (AWS Lambda, FastAPI, etc.)
    should implement authentication extraction and validation.
    """

    @abstractmethod
    async def extract_auth_context(self, *args: Any, **kwargs: Any) -> AuthContext:
        """
        Extract authentication context from the request.

        Args:
            *args: Positional arguments from the middleware call
            **kwargs: Keyword arguments from the middleware call

        Returns:
            AuthContext with extracted authentication data
        """

    @abstractmethod
    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """
        Extract request data from the middleware arguments.

        Args:
            *args: Positional arguments from the middleware call
            **kwargs: Keyword arguments from the middleware call

        Returns:
            Tuple of (request_data, context)
        """

    @abstractmethod
    def inject_auth_context(
        self, request_data: dict[str, Any], auth_context: AuthContext
    ) -> None:
        """
        Inject authentication context into the request data.

        Args:
            request_data: The request data to modify
            auth_context: The authentication context to inject
        """


class AWSLambdaAuthenticationStrategy(AuthenticationStrategy):
    """
    AWS Lambda-specific authentication strategy.

    Extracts authentication context from AWS Lambda events and context objects.
    """

    def __init__(
        self,
        iam_provider: UnifiedIAMProvider,
        caller_context: str | None = None,
    ):
        """
        Initialize AWS Lambda authentication strategy.

        Args:
            iam_provider: The IAM provider for user data
            caller_context: The calling context for IAM integration
        """
        self.iam_provider = iam_provider
        self.caller_context = caller_context

    async def extract_auth_context(self, *args: Any, **kwargs: Any) -> AuthContext:
        """
        Extract authentication context from AWS Lambda event and context.

        Args:
            *args: Positional arguments (event, context)
            **kwargs: Keyword arguments (event, context)

        Returns:
            AuthContext with extracted authentication data
        """
        event, context = self.get_request_data(*args, **kwargs)

        # Extract from AWS Lambda authorizer context
        authorizer_context = event.get("requestContext", {}).get("authorizer", {})
        claims = authorizer_context.get("claims", {})

        user_id = claims.get("sub")
        user_roles = self._extract_user_roles(claims)

        # If we have a caller context, fetch full user data from IAM
        user_object = None
        caller_context = getattr(self, "caller_context", None)
        if user_id and caller_context:
            try:
                response = await self.iam_provider.get_user(user_id, caller_context)
                if response.get("statusCode") == HTTP_OK:
                    user_object = response["body"]
            except Exception:
                # Log error but continue with basic auth context
                pass

        # Determine authentication status
        is_authenticated = bool(
            user_id and isinstance(user_id, str) and user_id.strip()
        )  # Only require valid string user_id for authentication

        # Add AWS Lambda context information to metadata
        metadata = {
            "authorizer": authorizer_context,
            "claims": claims,
        }

        if hasattr(context, "function_name"):
            metadata["function_name"] = context.function_name
        if hasattr(context, "request_id"):
            metadata["request_id"] = context.request_id

        return AuthContext(
            user_id=user_id,
            user_roles=user_roles,
            is_authenticated=is_authenticated,
            metadata=metadata,
            user_object=user_object,
            caller_context=caller_context,
        )

    def get_request_data(self, *args: Any, **kwargs: Any) -> tuple[dict[str, Any], Any]:
        """
        Extract AWS Lambda event and context from middleware arguments.

        Args:
            *args: Positional arguments (event, context)
            **kwargs: Keyword arguments (event, context)

        Returns:
            Tuple of (event, context)
        """
        event: dict[str, Any] | None = (
            kwargs.get("event") if "event" in kwargs else args[0]
        )
        context: Any = kwargs.get("context") if "context" in kwargs else args[1]

        if not event or not context:
            error_message = "Event and context are required"
            raise ValueError(error_message)

        return event, context

    def inject_auth_context(
        self, request_data: dict[str, Any], auth_context: AuthContext
    ) -> None:
        """
        Inject authentication context into AWS Lambda event.

        Args:
            request_data: The AWS Lambda event dictionary
            auth_context: The authentication context to inject
        """
        request_data["_auth_context"] = auth_context

    def _extract_user_roles(self, claims: dict[str, Any]) -> list[str]:
        """
        Extract user roles from JWT claims.

        Args:
            claims: JWT claims dictionary

        Returns:
            List of user roles
        """
        # Extract roles from common JWT claim patterns
        roles = []

        # Check for custom claims
        if "custom:roles" in claims:
            roles_str = claims["custom:roles"]
            if isinstance(roles_str, str):
                roles = [role.strip() for role in roles_str.split(",") if role.strip()]

        # Check for standard claims
        if "cognito:groups" in claims:
            groups = claims["cognito:groups"]
            if isinstance(groups, list):
                roles.extend(groups)
            elif isinstance(groups, str):
                roles.extend(
                    [group.strip() for group in groups.split(",") if group.strip()]
                )

        # Check for scope-based roles
        if "scope" in claims:
            scope = claims["scope"]
            if isinstance(scope, str):
                # Convert OAuth scopes to roles
                scopes = [s.strip() for s in scope.split() if s.strip()]
                roles.extend(scopes)

        return list(set(roles))  # Remove duplicates

    async def cleanup(self) -> None:
        """Clean up strategy-specific resources."""
        self.iam_provider.clear_cache()


class AuthenticationMiddleware(BaseMiddleware):
    """Generic authentication middleware that uses composition for different strategies.

    Provides simple, consistent authentication across different platforms while
    maintaining the composable architecture. It delegates platform-specific
    authentication logic to strategy objects.

    Attributes:
        strategy: The authentication strategy to use.
        policy: Authentication policy configuration.

    Notes:
        Order: runs early in middleware chain (before business logic).
        Propagates cancellation: Yes.
        Adds headers: Authorization context.
        Retries: None; Timeout: configurable per instance.
    """

    def __init__(
        self,
        *,
        strategy: AuthenticationStrategy,
        policy: AuthPolicy | None = None,
        name: str | None = None,
        timeout: float | None = None,
    ):
        """Initialize authentication middleware.

        Args:
            strategy: The authentication strategy to use.
            policy: Authentication policy configuration.
            name: Optional name for the middleware.
            timeout: Optional timeout for authentication operations.
        """
        super().__init__(name=name, timeout=timeout)
        self.strategy = strategy
        self.policy = policy or AuthPolicy()

    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute authentication middleware around the handler.

        Args:
            handler: The next handler in the middleware chain.
            *args: Positional arguments passed to the middleware.
            **kwargs: Keyword arguments passed to the middleware.

        Returns:
            The response from the handler (potentially modified).

        Raises:
            AuthenticationError: When authentication fails.
            AuthorizationError: When authorization fails.

        Notes:
            Extracts auth context, validates authentication and authorization,
            injects auth context into request data, and executes handler.
        """
        try:
            # Extract authentication context using the strategy
            auth_context = await self.strategy.extract_auth_context(*args, **kwargs)

            # Check if authentication is required and bypass conditions
            if self._should_require_authentication():
                self._validate_authentication(auth_context)
                self._validate_authorization(auth_context)

            # Get request data and inject auth context
            request_data, context = self.strategy.get_request_data(*args, **kwargs)
            self.strategy.inject_auth_context(request_data, auth_context)

            # Execute the handler with authentication context available
            return await handler(request_data, context)

        finally:
            # Clean up any strategy-specific resources
            cleanup_method = getattr(self.strategy, "cleanup", None)
            if cleanup_method is not None:
                await cleanup_method()

    def _validate_authentication(self, auth_context: AuthContext) -> None:
        """Validate that the user is authenticated."""
        if not auth_context.is_authenticated:
            # Security Event: Authentication failure
            logger.warning(
                "Authentication failed - user not authenticated",
                security_event="authentication_failure",
                security_level="medium",
                auth_required=True,
                user_authenticated=auth_context.is_authenticated,
                business_impact="access_denied",
                action="validate_authentication_failed",
            )
            raise AuthenticationError(AUTHENTICATION_REQUIRED_MSG)
        else:
            # Security Event: Authentication success
            logger.info(
                "Authentication successful",
                security_event="authentication_success",
                security_level="info",
                user_authenticated=auth_context.is_authenticated,
                user_roles_count=(
                    len(auth_context.user_roles) if auth_context.user_roles else 0
                ),
                business_context="access_control",
                action="validate_authentication_success",
            )

    def _validate_authorization(self, auth_context: AuthContext) -> None:
        """Validate that the user has required roles."""
        if not self.policy.has_required_role(auth_context.user_roles):
            # Security Event: Authorization failure
            logger.warning(
                "Authorization failed - insufficient permissions",
                security_event="authorization_failure",
                security_level="high",
                required_roles=(
                    list(self.policy.allowed_roles) if self.policy.allowed_roles else []
                ),
                user_roles_count=(
                    len(auth_context.user_roles) if auth_context.user_roles else 0
                ),
                business_impact="access_denied",
                action="validate_authorization_failed",
            )
            raise AuthorizationError(INSUFFICIENT_PERMISSIONS_MSG)
        else:
            # Security Event: Authorization success
            logger.info(
                "Authorization successful",
                security_event="authorization_success",
                security_level="info",
                required_roles_count=(
                    len(self.policy.allowed_roles) if self.policy.allowed_roles else 0
                ),
                user_roles_count=(
                    len(auth_context.user_roles) if auth_context.user_roles else 0
                ),
                business_context="access_control",
                action="validate_authorization_success",
            )

    def _should_require_authentication(self) -> bool:
        """Determine if authentication should be required for this request.

        Returns:
            True if authentication should be required.
        """
        return self.policy.is_authenticated_required()

    async def _cleanup(self) -> None:
        """Clean up any strategy-specific resources.

        Notes:
            Default implementation does nothing.
            Override in subclasses if needed.
        """
        # Default implementation does nothing
        # Override in subclasses if needed

    def get_auth_context(self, request_data: dict[str, Any]) -> AuthContext | None:
        """Get authentication context from request data.

        Args:
            request_data: The request data dictionary.

        Returns:
            AuthContext if available, None otherwise.
        """
        return request_data.get("_auth_context")


# Convenience function for creating authentication middleware
def create_auth_middleware(
    *,
    strategy: AuthenticationStrategy,
    require_authentication: bool = True,
    allowed_roles: list[str] | None = None,
    caller_context: str | None = None,
    name: str | None = None,
    timeout: float | None = None,
) -> AuthenticationMiddleware:
    """Create authentication middleware with common configuration.

    Args:
        strategy: The authentication strategy to use.
        require_authentication: Whether authentication is required.
        allowed_roles: List of allowed roles.
        caller_context: The calling context for IAM integration.
        name: Optional middleware name.
        timeout: Optional timeout for auth operations.

    Returns:
        Configured AuthenticationMiddleware instance.

    Notes:
        Creates AuthPolicy and AuthenticationMiddleware with specified configuration.
        Provides a convenient factory function for common authentication setups.
    """
    policy = AuthPolicy(
        require_authentication=require_authentication,
        allowed_roles=allowed_roles,
        caller_context=caller_context,
    )

    return AuthenticationMiddleware(
        strategy=strategy,
        policy=policy,
        name=name,
        timeout=timeout,
    )


# Context-specific factory functions for AWS Lambda
def products_aws_auth_middleware() -> AuthenticationMiddleware:
    """Create auth middleware for products catalog context.

    Returns:
        Configured AuthenticationMiddleware for products catalog with AWS Lambda strategy.

    Notes:
        Uses UnifiedIAMProvider with products_catalog caller context and container-scoped caching.
        Requires authentication by default.
        Optimized for AWS Lambda containers with persistent cache across requests.
        FastAPI: Not thread-safe - requires request-scoped instances.
    """
    iam_provider = UnifiedIAMProvider(
        logger_name="products_iam",
        cache_strategy="container",  # Optimized for Lambda containers
    )
    strategy = AWSLambdaAuthenticationStrategy(iam_provider, "products_catalog")

    return create_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="products_catalog",
    )


def recipes_aws_auth_middleware() -> AuthenticationMiddleware:
    """Create auth middleware for recipes catalog context.

    Returns:
        Configured AuthenticationMiddleware for recipes catalog with AWS Lambda strategy.

    Notes:
        Uses UnifiedIAMProvider with recipes_catalog caller context and container-scoped caching.
        Requires authentication by default.
        Optimized for AWS Lambda containers with persistent cache across requests.
        FastAPI: Not thread-safe - requires request-scoped instances.
    """
    iam_provider = UnifiedIAMProvider(
        logger_name="recipes_iam",
        cache_strategy="container",  # Optimized for Lambda containers
    )
    strategy = AWSLambdaAuthenticationStrategy(iam_provider, "recipes_catalog")

    return create_auth_middleware(
        strategy=strategy, require_authentication=True, caller_context="recipes_catalog"
    )


def client_onboarding_aws_auth_middleware() -> AuthenticationMiddleware:
    """Create auth middleware for client onboarding context.

    Returns:
        Configured AuthenticationMiddleware for client onboarding with AWS Lambda strategy.

    Notes:
        Uses UnifiedIAMProvider with client_onboarding caller context and container-scoped caching.
        Requires authentication by default.
        Optimized for AWS Lambda containers with persistent cache across requests.
        FastAPI: Not thread-safe - requires request-scoped instances.
    """
    iam_provider = UnifiedIAMProvider(
        logger_name="client_onboarding_iam",
        cache_strategy="container",  # Optimized for Lambda containers
    )
    strategy = AWSLambdaAuthenticationStrategy(iam_provider, "client_onboarding")

    return create_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="client_onboarding",
    )


def iam_aws_auth_middleware() -> AuthenticationMiddleware:
    """Create auth middleware for IAM context with AWS Lambda strategy.

    Returns:
        Configured AuthenticationMiddleware for IAM with AWS Lambda strategy.

    Notes:
        Uses UnifiedIAMProvider with iam caller context and container-scoped caching.
        Requires authentication by default.
        Optimized for AWS Lambda containers with persistent cache across requests.
        FastAPI: Not thread-safe - requires request-scoped instances.
    """
    iam_provider = UnifiedIAMProvider(
        logger_name="iam_auth",
        cache_strategy="container",  # Optimized for Lambda containers
    )
    strategy = AWSLambdaAuthenticationStrategy(iam_provider, "iam")

    return create_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="iam",
    )
