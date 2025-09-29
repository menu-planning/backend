"""FastAPI native error handling using exception handlers.

This module provides FastAPI-specific error handling using the native exception
handler pattern instead of middleware, following FastAPI best practices.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
)

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """Setup FastAPI exception handlers for consistent error responses.
    
    Args:
        app: FastAPI application instance to add exception handlers to
        
    Notes:
        This function adds exception handlers for:
        - HTTP exceptions (4xx, 5xx status codes)
        - Request validation errors (422)
        - General exceptions (500)
        
        All handlers return consistent JSON error responses with structured
        error information and proper logging.
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions with consistent JSON responses.
        
        Args:
            request: FastAPI Request object
            exc: Starlette HTTPException instance
            
        Returns:
            JSONResponse with structured error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "HTTP exception occurred",
            extra={
                "status_code": exc.status_code,
                "detail": str(exc.detail),
                **request_context,
            }
        )
        
        # Determine error type based on status code
        error_type = _get_error_type_from_status_code(exc.status_code)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": error_type,
                "message": str(exc.detail),
                "status_code": exc.status_code,
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle validation errors with detailed error information.
        
        Args:
            request: FastAPI Request object
            exc: RequestValidationError instance
            
        Returns:
            JSONResponse with validation error details
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "Validation error occurred",
            extra={
                "errors": exc.errors(),
                "body": exc.body,
                **request_context,
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions.
        
        Args:
            request: FastAPI Request object
            exc: Exception instance
            
        Returns:
            JSONResponse with generic error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.error(
            "Unexpected error occurred",
            extra={
                "error": str(exc),
                "error_type": type(exc).__name__,
                **request_context,
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            }
        )
    
    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        """Handle EntityNotFoundError as 404 Not Found.
        
        Args:
            request: FastAPI Request object
            exc: EntityNotFoundError instance
            
        Returns:
            JSONResponse with not found error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "Entity not found",
            extra={
                "entity_id": getattr(exc, "id", "unknown"),
                "repository": str(getattr(exc, "repository", "unknown")),
                **request_context,
            }
        )
        
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found_error",
                "message": f"Entity not found: {str(exc)}",
                "status_code": 404,
            }
        )
    
    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
        """Handle KeyError as 404 Not Found.
        
        Args:
            request: FastAPI Request object
            exc: KeyError instance
            
        Returns:
            JSONResponse with not found error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "Resource not found (KeyError)",
            extra={
                "missing_key": str(exc),
                **request_context,
            }
        )
        
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found_error",
                "message": f"Resource not found: {str(exc)}",
                "status_code": 404,
            }
        )
    
    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        """Handle PermissionError as 403 Forbidden.
        
        Args:
            request: FastAPI Request object
            exc: PermissionError instance
            
        Returns:
            JSONResponse with authorization error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "Permission denied",
            extra={
                "permission_error": str(exc),
                **request_context,
            }
        )
        
        return JSONResponse(
            status_code=403,
            content={
                "error": "authorization_error",
                "message": f"Permission denied: {str(exc)}",
                "status_code": 403,
            }
        )
    
    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
        """Handle TimeoutError as 408 Request Timeout.
        
        Args:
            request: FastAPI Request object
            exc: TimeoutError instance
            
        Returns:
            JSONResponse with timeout error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "Request timeout",
            extra={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                **request_context,
            }
        )
        
        return JSONResponse(
            status_code=408,
            content={
                "error": "timeout_error",
                "message": f"Request timeout: {str(exc)}",
                "status_code": 408,
            }
        )
    
    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError) -> JSONResponse:
        """Handle ConnectionError as 408 Request Timeout.
        
        Args:
            request: FastAPI Request object
            exc: ConnectionError instance
            
        Returns:
            JSONResponse with timeout error information
        """
        # Extract request context for logging
        request_context = _extract_request_context(request)
        
        logger.warning(
            "Connection error",
            extra={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                **request_context,
            }
        )
        
        return JSONResponse(
            status_code=408,
            content={
                "error": "timeout_error",
                "message": f"Connection error: {str(exc)}",
                "status_code": 408,
            }
        )


def _extract_request_context(request: Request) -> dict[str, Any]:
    """Extract request context information for logging.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dictionary with request context information
    """
    context = {
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    
    # Add correlation ID if available
    correlation_id = request.headers.get("x-correlation-id")
    if correlation_id:
        context["correlation_id"] = correlation_id
    
    # Add user context if available
    if hasattr(request, "state") and hasattr(request.state, "user"):
        context["user_id"] = getattr(request.state.user, "id", None)
    
    return context


def _get_error_type_from_status_code(status_code: int) -> str:
    """Get error type string based on HTTP status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Error type string
    """
    if 400 <= status_code < 500:
        if status_code == 400:
            return "business_rule_error"
        elif status_code == 401:
            return "authentication_error"
        elif status_code == 403:
            return "authorization_error"
        elif status_code == 404:
            return "not_found_error"
        elif status_code == 408:
            return "timeout_error"
        elif status_code == 409:
            return "conflict_error"
        elif status_code == 422:
            return "validation_error"
        else:
            return "client_error"
    elif 500 <= status_code < 600:
        return "server_error"
    else:
        return "http_error"


# Convenience function for creating custom HTTP exceptions
def create_http_exception(
    status_code: int,
    message: str,
    error_type: str | None = None,
) -> HTTPException:
    """Create a custom HTTPException with structured error information.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_type: Optional error type (auto-detected if not provided)
        
    Returns:
        HTTPException instance
    """
    if error_type is None:
        error_type = _get_error_type_from_status_code(status_code)
    
    detail = {
        "error": error_type,
        "message": message,
        "status_code": status_code,
    }
    
    return HTTPException(status_code=status_code, detail=detail)
