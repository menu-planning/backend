"""
Auth middleware for unified authentication and authorization.

This middleware provides standardized authentication and authorization across all endpoints by:
- Extracting and validating user context from AWS Lambda events
- Unified IAMProvider integration with request-scoped caching
- Permission checking with context-aware business logic
- Integration with error middleware for consistent auth error responses
- Maintaining backward compatibility with existing IAMProvider patterns
- Localstack development environment bypass
"""

import os
import json
from typing import Any, Dict, Callable, Awaitable, Optional, Union, List
from contextlib import asynccontextmanager

from src.logging.logger import correlation_id_ctx, StructlogFactory
from src.contexts.shared_kernel.schemas.error_response import ErrorType
import src.contexts.iam.core.endpoints.internal.get as iam_internal_api


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class AuthContext:
    """Container for authentication context and user data."""
    
    def __init__(
        self,
        user_id: str,
        user_object: Any = None,
        is_authenticated: bool = True,
        caller_context: Optional[str] = None
    ):
        self.user_id = user_id
        self.user_object = user_object  # This should be a SeedUser object or None
        self.is_authenticated = is_authenticated
        self.caller_context = caller_context

    @property
    def user(self):
        """Get SeedUser object."""
        return self.user_object

    def has_permission(self, permission: str, context: Optional[str] = None) -> bool:
        """Check if user has specific permission, optionally in a specific context."""
        if not self.is_authenticated or not self.user:
            return False
        
        # For IAM context, use context-specific permission checking
        if context:
            return self.user.has_permission(context, permission)
        else:
            return self.user.has_permission(permission)

    def is_owner_or_has_permission(self, resource_owner_id: str, permission: str) -> bool:
        """Check if user is the resource owner OR has the specified permission."""
        if not self.is_authenticated:
            return False
        
        return (self.user_id == resource_owner_id or 
                self.has_permission(permission))


class UnifiedIAMProvider:
    """
    Unified IAMProvider that consolidates all context-specific implementations.
    
    Features:
    - Single source of truth for IAM integration
    - Request-scoped caching to reduce IAM calls
    - Consistent error handling and logging
    - Context-aware user data filtering
    - Backward compatibility with existing patterns
    """
    
    def __init__(self, logger_name: str = "iam_provider"):
        # Ensure structlog is configured
        StructlogFactory.configure()
        self.structured_logger = StructlogFactory.get_logger(logger_name)
        self._cache = {}  # Request-scoped cache

    async def get_user(self, user_id: str, caller_context: str) -> Dict[str, Any]:
        """
        Get user data from IAM with caching and error handling.
        
        Args:
            user_id: The user ID to fetch
            caller_context: The calling context (e.g., "products_catalog", "recipes_catalog")
            
        Returns:
            Dictionary with statusCode and body (SeedUser object on success)
            
        Raises:
            AuthenticationError: When IAM call fails
        """
        # Validate caller_context first
        if caller_context not in ["products_catalog", "recipes_catalog"]:
            error_message = f"Unsupported caller context: {caller_context}. Supported contexts: 'products_catalog', 'recipes_catalog'"
            correlation_id = correlation_id_ctx.get() or "unknown"
            self.structured_logger.warning(
                "Unsupported caller context requested",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                supported_contexts=["products_catalog", "recipes_catalog"]
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": error_message})
            }

        # Check cache first (request-scoped)
        cache_key = f"{user_id}:{caller_context}"
        correlation_id = correlation_id_ctx.get() or "unknown"
        
        if cache_key in self._cache:
            self.structured_logger.debug(
                "IAM user data retrieved from cache",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context
            )
            return self._cache[cache_key]

        try:
            self.structured_logger.debug(
                "Fetching user data from IAM",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context
            )
            
            # Call internal IAM endpoint
            response = await iam_internal_api.get(id=user_id, caller_context=caller_context)
            
            if response.get("statusCode") != 200:
                self.structured_logger.warning(
                    "IAM provider returned error",
                    correlation_id=correlation_id,
                    user_id=user_id,
                    caller_context=caller_context,
                    status_code=response.get("statusCode"),
                    response_body=response.get("body")
                )
                # Cache error response to avoid repeated failed calls
                self._cache[cache_key] = response
                return response
           
            # Convert via appropriate context-specific IAMUser schema
            if caller_context == "products_catalog":
                from src.contexts.products_catalog.core.adapters.internal_providers.iam.api_schemas.api_user import ApiUser
            elif caller_context == "recipes_catalog":
                from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api_schemas.api_user import ApiUser
                
            iam_user = ApiUser.model_validate_json(response["body"]) # type: ignore
            seed_user = iam_user.to_domain()
            
            # Create successful response
            success_response = {"statusCode": 200, "body": seed_user}
            
            # Cache successful response
            self._cache[cache_key] = success_response
            
            self.structured_logger.info(
                "User authenticated successfully",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                user_roles_count=len(iam_user.roles)
            )
            
            return success_response
            
        except Exception as e:
            self.structured_logger.error(
                "IAM provider call failed",
                correlation_id=correlation_id,
                user_id=user_id,
                caller_context=caller_context,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )
            # Return error response compatible with existing patterns
            error_response = {
                "statusCode": 500,
                "body": json.dumps({"message": "Authentication service error"})
            }
            return error_response

    def clear_cache(self):
        """Clear request-scoped cache (called at request end)."""
        self._cache.clear()


class AuthMiddleware:
    """
    Middleware for standardized authentication and authorization.
    
    Features:
    - Unified IAMProvider integration with caching
    - Localstack development bypass
    - Context-aware permission checking
    - Integration with error middleware for auth errors
    - Backward compatibility with existing auth patterns
    - Request-scoped user context management
    """
    
    def __init__(
        self,
        caller_context: str,
        require_authentication: bool = True,
        logger_name: str = "auth_middleware"
    ):
        """
        Initialize auth middleware.
        
        Args:
            caller_context: The calling context (e.g., "products_catalog", "recipes_catalog")
            require_authentication: Whether to require authentication for all requests
            logger_name: Name for auth logger instance
        """
        # Ensure structlog is configured
        StructlogFactory.configure()
        
        self.structured_logger = StructlogFactory.get_logger(logger_name)
        self.caller_context = caller_context
        self.require_authentication = require_authentication
        self.iam_provider = UnifiedIAMProvider()
        
        # Current request auth context
        self._current_auth_context: Optional[AuthContext] = None

    async def __call__(
        self,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute auth middleware around endpoint handler.
        
        Args:
            handler: The endpoint handler function to wrap
            event: AWS Lambda event dictionary
            
        Returns:
            Either successful response from handler or authentication error response
        """
        correlation_id = correlation_id_ctx.get() or "unknown"
        
        try:
            # Check for localstack bypass
            is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
            
            if is_localstack:
                self.structured_logger.debug(
                    "Localstack detected - bypassing authentication",
                    correlation_id=correlation_id,
                    caller_context=self.caller_context
                )
                # Create mock auth context for localstack
                self._current_auth_context = AuthContext(
                    user_id="localstack-user",
                    user_object=None, # Mock user object
                    is_authenticated=False,
                    caller_context=self.caller_context
                )
            else:
                # Perform authentication
                auth_context = await self._authenticate_user(event)
                self._current_auth_context = auth_context
                
                if self.require_authentication and not auth_context.is_authenticated:
                    raise AuthenticationError("Authentication required")

            # Execute the handler with auth context available
            response = await handler(event)
            return response
            
        except AuthenticationError as e:
            return await self._handle_auth_error(e, "authentication_failed", 401)
        except AuthorizationError as e:
            return await self._handle_auth_error(e, "authorization_failed", 403)
        except Exception as e:
            # Re-raise other exceptions to be handled by error middleware
            raise
        finally:
            # Clear request-scoped cache
            self.iam_provider.clear_cache()
            self._current_auth_context = None

    async def _authenticate_user(self, event: Dict[str, Any]) -> AuthContext:
        """
        Authenticate user from AWS Lambda event.
        
        Args:
            event: AWS Lambda event dictionary
            
        Returns:
            AuthContext with user data and authentication status
        """
        correlation_id = correlation_id_ctx.get() or "unknown"
        
        try:
            # Extract user ID from authorizer context
            authorizer_context = event.get("requestContext", {}).get("authorizer", {})
            claims = authorizer_context.get("claims", {})
            user_id = claims.get("sub")
            
            if not user_id:
                self.structured_logger.warning(
                    "No user ID found in authorizer context",
                    correlation_id=correlation_id,
                    caller_context=self.caller_context,
                    authorizer_context=authorizer_context
                )
                return AuthContext(
                    user_id="",
                    user_object=None, # Mock user object
                    is_authenticated=False,
                    caller_context=self.caller_context
                )

            # Get user data from IAM
            response = await self.iam_provider.get_user(user_id, self.caller_context)
            
            if response.get("statusCode") != 200:
                self.structured_logger.warning(
                    "IAM authentication failed",
                    correlation_id=correlation_id,
                    user_id=user_id,
                    caller_context=self.caller_context,
                    iam_status_code=response.get("statusCode")
                )
                # For backward compatibility, raise exception with IAM response
                raise AuthenticationError(f"IAM authentication failed: {response.get('body', 'Unknown error')}")

            # Extract user object from IAM response
            seed_user = response["body"]
            
            return AuthContext(
                user_id=user_id,
                user_object=seed_user,
                is_authenticated=True,
                caller_context=self.caller_context
            )
            
        except Exception as e:
            self.structured_logger.error(
                "Authentication error",
                correlation_id=correlation_id,
                caller_context=self.caller_context,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    async def _handle_auth_error(
        self, 
        error: Exception, 
        error_context: str, 
        status_code: int
    ) -> Dict[str, Any]:
        """
        Handle authentication/authorization errors with consistent response format.
        
        Args:
            error: The auth error that occurred
            error_context: Context description for logging
            status_code: HTTP status code for response
            
        Returns:
            Standardized error response dictionary
        """
        correlation_id = correlation_id_ctx.get() or "unknown"
        
        self.structured_logger.warning(
            f"Authentication/authorization failed: {error_context}",
            correlation_id=correlation_id,
            caller_context=self.caller_context,
            error_message=str(error),
            status_code=status_code
        )
        
        # Return consistent error response with CORS headers
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT"
            },
            "body": json.dumps({
                "message": str(error),
                "correlation_id": correlation_id
            })
        }

    @property
    def current_user(self) -> Optional[AuthContext]:
        """Get current authenticated user context."""
        return self._current_auth_context

    def require_permission(self, permission: str, context: Optional[str] = None):
        """
        Decorator for requiring specific permissions on endpoint methods.
        
        Usage:
            @auth_middleware.require_permission("MANAGE_RECIPES")
            async def create_recipe(event):
                # This will only execute if user has MANAGE_RECIPES permission
        """
        def decorator(handler_func):
            async def wrapper(*args, **kwargs):
                if not self._current_auth_context or not self._current_auth_context.is_authenticated:
                    raise AuthenticationError("Authentication required")
                
                if not self._current_auth_context.has_permission(permission, context):
                    raise AuthorizationError(f"Permission required: {permission}")
                    
                return await handler_func(*args, **kwargs)
            return wrapper
        return decorator

    def require_owner_or_permission(self, resource_owner_id: str, permission: str):
        """
        Require that user is either the resource owner OR has the specified permission.
        
        Args:
            resource_owner_id: ID of the resource owner
            permission: Required permission if not owner
        """
        if not self._current_auth_context or not self._current_auth_context.is_authenticated:
            raise AuthenticationError("Authentication required")
        
        if not self._current_auth_context.is_owner_or_has_permission(resource_owner_id, permission):
            raise AuthorizationError(f"Must be resource owner or have permission: {permission}")

    @asynccontextmanager
    async def auth_context(self, operation_name: str = "operation"):
        """
        Context manager for accessing auth context in specific code blocks.
        
        Usage:
            async with auth_middleware.auth_context("user_validation"):
                user_id = auth_middleware.current_user.user_id
                # Code that needs auth context
        
        Args:
            operation_name: Name of the operation for logging context
        """
        correlation_id = correlation_id_ctx.get() or "unknown"
        
        if not self._current_auth_context:
            self.structured_logger.warning(
                f"No auth context available for {operation_name}",
                correlation_id=correlation_id,
                operation=operation_name
            )
        
        try:
            yield self._current_auth_context
        except Exception as e:
            self.structured_logger.error(
                f"Error in auth context for {operation_name}",
                correlation_id=correlation_id,
                operation=operation_name,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )
            raise


# Factory functions for different auth middleware configurations

def create_auth_middleware(
    caller_context: str,
    require_authentication: bool = True
) -> AuthMiddleware:
    """
    Create auth middleware with standard configuration.
    
    Args:
        caller_context: The calling context (e.g., "products_catalog", "recipes_catalog")
        require_authentication: Whether to require authentication for all requests
        
    Returns:
        Configured AuthMiddleware instance
    """
    return AuthMiddleware(
        caller_context=caller_context,
        require_authentication=require_authentication
    )

def products_auth_middleware() -> AuthMiddleware:
    """
    Create auth middleware for products catalog context.
    
    Returns:
        Products-configured AuthMiddleware instance
    """
    return AuthMiddleware(
        caller_context="products_catalog",
        require_authentication=True
    )

def recipes_auth_middleware() -> AuthMiddleware:
    """
    Create auth middleware for recipes catalog context.
    
    Returns:
        Recipes-configured AuthMiddleware instance
    """
    return AuthMiddleware(
        caller_context="recipes_catalog",
        require_authentication=True
    )

def iam_auth_middleware() -> AuthMiddleware:
    """
    Create auth middleware for IAM context operations.
    
    Note: IAM operations currently use recipes_catalog context for authentication
    since IAM context is not supported in the UnifiedIAMProvider.
    
    Returns:
        IAM-configured AuthMiddleware instance using recipes_catalog context
    """
    return AuthMiddleware(
        caller_context="recipes_catalog",  # IAM operations use recipes_catalog context
        require_authentication=True
    )

def optional_auth_middleware(caller_context: str) -> AuthMiddleware:
    """
    Create auth middleware that doesn't require authentication (useful for public endpoints).
    
    Args:
        caller_context: The calling context
        
    Returns:
        Optional-auth configured AuthMiddleware instance
    """
    return AuthMiddleware(
        caller_context=caller_context,
        require_authentication=False
    )

# Backward compatibility helpers

async def get_current_user_legacy(event: Dict[str, Any], caller_context: str) -> Dict[str, Any]:
    """
    Legacy helper function that mimics the old IAMProvider.get() pattern.
    
    This function maintains backward compatibility with existing endpoint patterns
    while using the new unified auth middleware internally.
    
    Args:
        event: AWS Lambda event dictionary
        caller_context: The calling context
        
    Returns:
        Dictionary with statusCode and body (SeedUser object on success)
    """
    provider = UnifiedIAMProvider()
    
    try:
        # Extract user ID like the old pattern
        authorizer_context = event.get("requestContext", {}).get("authorizer", {})
        user_id = authorizer_context.get("claims", {}).get("sub")
        
        if not user_id:
            return {
                "statusCode": 401,
                "body": json.dumps({"message": "User ID not found in authorization context"})
            }
        
        # Use unified provider
        return await provider.get_user(user_id, caller_context)
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Authentication error: {str(e)}"})
        }
    finally:
        # Clean up cache
        provider.clear_cache() 