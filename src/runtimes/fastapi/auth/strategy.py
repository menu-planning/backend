"""
FastAPI authentication strategy and IAM provider integration.

This module provides FastAPI-specific authentication strategy that works with
the existing UnifiedIAMProvider from shared_kernel, following the same pattern
as AWSLambdaAuthenticationStrategy.
"""

from typing import Any
from datetime import datetime, timezone

from fastapi import Request
from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthenticationStrategy,
    AuthContext,
    UnifiedIAMProvider,
)
from src.logging.logger import get_logger

from .user_context import UserContext
from .jwt_validator import CognitoJWTValidator, JWTValidationError

logger = get_logger(__name__)

# HTTP status codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401


class FastAPIAuthenticationStrategy(AuthenticationStrategy):
    """
    FastAPI-specific authentication strategy.
    
    Extracts authentication context from FastAPI Request objects and integrates
    with the existing UnifiedIAMProvider to get user domain models.
    """
    
    def __init__(
        self,
        iam_provider: UnifiedIAMProvider,
        caller_context: str | None = None,
        jwt_validator: CognitoJWTValidator | None = None,
    ):
        """
        Initialize FastAPI authentication strategy.
        
        Args:
            iam_provider: The IAM provider for user data
            caller_context: The calling context for IAM integration
            jwt_validator: Optional JWT validator instance (creates default if None)
        """
        self.iam_provider = iam_provider
        self.caller_context = caller_context
        self.jwt_validator = jwt_validator or CognitoJWTValidator()
    
    async def extract_auth_context(self, *args: Any, **kwargs: Any) -> AuthContext:
        """
        Extract authentication context from FastAPI Request.
        
        Args:
            *args: Positional arguments (request)
            **kwargs: Keyword arguments (request)
            
        Returns:
            AuthContext with extracted authentication data
        """
        request_data, request = self.get_request_data(*args, **kwargs)
        
        # Extract user ID from JWT token or other auth mechanism
        user_id = await self._extract_user_id_from_request(request)
        user_roles = await self._extract_user_roles_from_request(request)
        
        # If we have a caller context, fetch full user data from IAM
        user_object = None
        caller_context = getattr(self, "caller_context", None)
        if user_id and caller_context:
            try:
                response = await self.iam_provider.get_user(user_id, caller_context)
                if response.get("statusCode") == HTTP_OK:
                    user_object = response["body"]
            except Exception as e:
                logger.warning(
                    "Failed to fetch user from IAM",
                    extra={
                        "user_id": user_id,
                        "caller_context": caller_context,
                        "error": str(e),
                    }
                )
                # Continue with basic auth context
        
        # Determine authentication status
        is_authenticated = bool(
            user_id and isinstance(user_id, str) and user_id.strip()
        )
        
        # Add FastAPI request information to metadata
        metadata = {
            "request_url": str(request.url),
            "request_method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        }
        
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
        Extract request data from the middleware arguments.
        
        Args:
            *args: Positional arguments (request)
            **kwargs: Keyword arguments (request)
            
        Returns:
            Tuple of (request_data, context) as required by the interface
        """
        request: Request | None = (
            kwargs.get("request") if "request" in kwargs else args[0]
        )
        
        if not request or not isinstance(request, Request):
            error_message = "FastAPI Request object is required"
            raise ValueError(error_message)
        
        # Convert FastAPI Request to dict format for compatibility
        request_data = {
            "request": request,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
        }
        
        return request_data, request
    
    def inject_auth_context(
        self, request_data: dict[str, Any], auth_context: AuthContext
    ) -> None:
        """
        Inject authentication context into the request data.
        
        Args:
            request_data: The request data to modify
            auth_context: The authentication context to inject
        """
        # Extract the FastAPI Request object from the request data
        request = request_data.get("request")
        if request and hasattr(request, 'state'):
            # Store auth context in request state for access in route handlers
            request.state.auth_context = auth_context
    
    async def _extract_user_id_from_request(self, request: Request) -> str | None:
        """
        Extract user ID from FastAPI request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            User ID if found, None otherwise
        """
        # Try to extract from Authorization header (JWT token)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            try:
                claims = await self.jwt_validator.validate_token(token)
                return claims.sub
            except JWTValidationError as e:
                logger.warning(
                    "JWT token validation failed",
                    extra={
                        "error": str(e),
                        "error_code": getattr(e, 'error_code', 'UNKNOWN'),
                    }
                )
                return None
        
        # Try to extract from custom headers
        user_id = request.headers.get("x-user-id")
        if user_id:
            return user_id
        
        # Try to extract from query parameters
        user_id = request.query_params.get("user_id")
        if user_id:
            return user_id
        
        return None
    
    async def _extract_user_roles_from_request(self, request: Request) -> list[str]:
        """
        Extract user roles from FastAPI request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            List of user roles
        """
        # Try to extract from JWT token first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            try:
                claims = await self.jwt_validator.validate_token(token)
                # Use the centralized role extraction from JWT validator
                return self.jwt_validator.extract_user_roles(claims)
            except JWTValidationError:
                # JWT validation failed, continue with other methods
                pass
        
        # Try to extract from custom headers
        roles_header = request.headers.get("x-user-roles")
        if roles_header:
            return [role.strip() for role in roles_header.split(",") if role.strip()]
        
        # Try to extract from query parameters
        roles_param = request.query_params.get("user_roles")
        if roles_param:
            return [role.strip() for role in roles_param.split(",") if role.strip()]
        
        return []
    
    
    async def cleanup(self) -> None:
        """Clean up strategy-specific resources."""
        self.iam_provider.clear_cache()


def get_fastapi_auth_strategy(caller_context: str) -> FastAPIAuthenticationStrategy:
    """
    Get FastAPI authentication strategy for a specific context.
    
    Args:
        caller_context: The calling context for IAM integration
        
    Returns:
        FastAPIAuthenticationStrategy: Configured strategy instance
        
    Notes:
        Creates a new UnifiedIAMProvider instance for each strategy.
        This follows the same pattern as the existing AWS Lambda factory functions.
    """
    iam_provider = UnifiedIAMProvider(
        logger_name=f"fastapi_iam_{caller_context}",
        cache_strategy="request",  # Use request-scoped caching for FastAPI
    )
    return FastAPIAuthenticationStrategy(iam_provider, caller_context)


async def get_user_from_iam(user_id: str, caller_context: str = "fastapi") -> UserContext | None:
    """
    Convenience function to get user from IAM context.
    
    Args:
        user_id: User identifier
        caller_context: Context for role filtering
        
    Returns:
        UserContext if user found, None otherwise
    """
    provider = UnifiedIAMProvider(
        logger_name=f"fastapi_iam_{caller_context}",
        cache_strategy="request",
    )
    response = await provider.get_user(user_id, caller_context)
    
    if response.get("statusCode") == HTTP_OK:
        # Convert domain user to UserContext
        domain_user = response["body"]
        return _convert_domain_user_to_context(domain_user)
    
    return None


def _convert_domain_user_to_context(domain_user: Any) -> UserContext:
    """
    Convert domain user to UserContext.
    
    Args:
        domain_user: Domain user object from IAM
        
    Returns:
        UserContext: Converted user context
    """
    # Extract roles from domain user
    roles = []
    if hasattr(domain_user, 'roles') and domain_user.roles:
        for role in domain_user.roles:
            if hasattr(role, 'name'):
                roles.append(role.name)
    
    # Create UserContext with basic information
    user_context = UserContext(
        user_id=domain_user.id if hasattr(domain_user, 'id') else "",
        username=domain_user.id if hasattr(domain_user, 'id') else "",
        cognito_username=domain_user.id if hasattr(domain_user, 'id') else "",
        token_use="access",
        issuer="iam-context",
        audience="fastapi",
        expires_at=datetime.now(tz=timezone.utc).replace(year=2099),
        issued_at=datetime.now(tz=timezone.utc),
        roles=roles,
        groups=[],
        preferred_role=roles[0] if roles else None,
        client_id="fastapi-internal",
        jti=f"iam-{domain_user.id if hasattr(domain_user, 'id') else ''}",
        origin_jti=None,
        identities=None,
        custom_roles=None,
    )
    
    return user_context


# Context-specific factory functions for FastAPI middleware
def products_fastapi_auth_middleware() -> type:
    """Create auth middleware for products catalog context with FastAPI strategy."""
    from src.runtimes.fastapi.middleware.auth import create_fastapi_auth_middleware
    
    strategy = get_fastapi_auth_strategy("products_catalog")
    
    return create_fastapi_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="products_catalog",
    )


def recipes_fastapi_auth_middleware() -> type:
    """Create auth middleware for recipes catalog context with FastAPI strategy."""
    from src.runtimes.fastapi.middleware.auth import create_fastapi_auth_middleware
    
    strategy = get_fastapi_auth_strategy("recipes_catalog")
    
    return create_fastapi_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="recipes_catalog",
    )


def client_onboarding_fastapi_auth_middleware() -> type:
    """Create auth middleware for client onboarding context with FastAPI strategy."""
    from src.runtimes.fastapi.middleware.auth import create_fastapi_auth_middleware
    
    strategy = get_fastapi_auth_strategy("client_onboarding")
    
    return create_fastapi_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="client_onboarding",
    )


def iam_fastapi_auth_middleware() -> type:
    """Create auth middleware for IAM context with FastAPI strategy."""
    from src.runtimes.fastapi.middleware.auth import create_fastapi_auth_middleware
    
    strategy = get_fastapi_auth_strategy("iam")
    
    return create_fastapi_auth_middleware(
        strategy=strategy,
        require_authentication=True,
        caller_context="iam",
    )
