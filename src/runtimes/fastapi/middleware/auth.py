"""
FastAPI authentication middleware for Cognito JWT tokens.

This module provides FastAPI middleware for JWT token validation and user context
extraction, using the shared authentication strategy from auth/strategy.py.
"""

import logging

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthPolicy,
)
from src.runtimes.fastapi.auth.strategy import FastAPIAuthenticationStrategy
from src.runtimes.fastapi.auth.errors import get_auth_error_handler

logger = logging.getLogger(__name__)


class FastAPIAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI authentication middleware for JWT token validation.
    
    This middleware validates Cognito JWT tokens and extracts user context,
    using the shared FastAPIAuthenticationStrategy from auth/strategy.py.
    """
    
    def __init__(
        self,
        app,
        *,
        strategy: FastAPIAuthenticationStrategy,
        policy: AuthPolicy | None = None,
        name: str | None = None,
    ):
        """
        Initialize FastAPI authentication middleware.
        
        Args:
            app: FastAPI application instance
            strategy: Authentication strategy for extracting auth context
            policy: Authentication policy for validation rules
            name: Optional name for the middleware
        """
        super().__init__(app)
        self.strategy = strategy
        self.policy = policy or AuthPolicy()
        self.name = name or "fastapi_auth"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process authentication for incoming requests.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in the chain
            
        Returns:
            FastAPI Response object
            
        Notes:
            This method delegates authentication logic to the strategy and policy,
            focusing only on middleware concerns like request/response processing.
        """
        try:
            # Extract authentication context using the strategy
            auth_context = await self.strategy.extract_auth_context(request)
            
            # Check if authentication is required and validate using policy
            if self._should_require_authentication(request):
                if not auth_context.is_authenticated:
                    logger.warning(
                        "Authentication required",
                        extra={
                            "path": request.url.path,
                            "method": request.method,
                            "user_id": auth_context.user_id,
                        }
                    )
                    return self._create_auth_error_response("Authentication required", 401)
                
                if not self.policy.has_required_role(auth_context.user_roles):
                    logger.warning(
                        "Insufficient permissions",
                        extra={
                            "path": request.url.path,
                            "method": request.method,
                            "user_id": auth_context.user_id,
                            "user_roles": auth_context.user_roles,
                            "required_roles": self.policy.allowed_roles,
                        }
                    )
                    return self._create_auth_error_response("Insufficient permissions", 403)
            
            # Inject auth context into request state
            self.strategy.inject_auth_context(request, auth_context)
            
            # Process the request
            response = await call_next(request)
            
            # Add auth context info to response headers for debugging (optional)
            if hasattr(request.state, "auth_context"):
                auth_ctx = request.state.auth_context
                if auth_ctx.is_authenticated:
                    response.headers["X-Auth-User"] = auth_ctx.user_id or ""
                    response.headers["X-Auth-Roles"] = ",".join(auth_ctx.user_roles)
                else:
                    response.headers["X-Auth-Status"] = "unauthenticated"
            
            return response
            
        except Exception as e:
            logger.error(
                "Authentication middleware error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            return self._create_auth_error_response("Internal server error", 500)
    
    def _should_require_authentication(self, request: Request) -> bool:
        """
        Determine if authentication should be required for this request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True if authentication should be required
        """
        # Skip authentication for health checks and other public endpoints
        if request.url.path in ["/health", "/healthz", "/ping", "/"]:
            return False
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return False
        
        return self.policy.is_authenticated_required()
    
    
    def _create_auth_error_response(self, message: str, status_code: int) -> Response:
        """
        Create a standardized authentication error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            
        Returns:
            FastAPI Response object
        """
        error_handler = get_auth_error_handler()
        
        # Use the comprehensive error handler for consistent error responses
        if status_code == 401:
            error_exception = error_handler.handle_authentication_required()
        elif status_code == 403:
            error_exception = error_handler.handle_authorization_failed()
        else:
            # For other status codes, create a generic error
            error_response = {
                "error": "authentication_error",
                "message": message,
                "status_code": status_code,
            }
            return JSONResponse(
                status_code=status_code,
                content=error_response,
                headers={
                    "Content-Type": "application/json",
                    "X-Error-Type": "authentication",
                }
            )
        
        # Extract the error response from the HTTPException
        error_detail = error_exception.detail
        if isinstance(error_detail, dict):
            return JSONResponse(
                status_code=error_exception.status_code,
                content=error_detail,
                headers={
                    "Content-Type": "application/json",
                    "X-Error-Type": "authentication",
                }
            )
        else:
            # Fallback for non-dict details
            return JSONResponse(
                status_code=error_exception.status_code,
                content={"error": "authentication_error", "message": str(error_detail)},
                headers={
                    "Content-Type": "application/json",
                    "X-Error-Type": "authentication",
                }
            )


def create_fastapi_auth_middleware(
    *,
    strategy: FastAPIAuthenticationStrategy,
    require_authentication: bool = True,
    allowed_roles: list[str] | None = None,
    caller_context: str | None = None,
    name: str | None = None,
) -> type[FastAPIAuthenticationMiddleware]:
    """
    Create FastAPI authentication middleware with common configuration.
    
    Args:
        strategy: The authentication strategy to use
        require_authentication: Whether authentication is required
        allowed_roles: List of allowed roles
        caller_context: The calling context for IAM integration
        name: Optional middleware name
        
    Returns:
        Configured FastAPIAuthenticationMiddleware class
        
    Notes:
        Creates AuthPolicy and FastAPIAuthenticationMiddleware with specified configuration.
        Provides a convenient factory function for common authentication setups.
    """
    policy = AuthPolicy(
        require_authentication=require_authentication,
        allowed_roles=allowed_roles,
        caller_context=caller_context,
    )
    
    class ConfiguredFastAPIAuthenticationMiddleware(FastAPIAuthenticationMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                strategy=strategy,
                policy=policy,
                name=name,
            )
    
    return ConfiguredFastAPIAuthenticationMiddleware

