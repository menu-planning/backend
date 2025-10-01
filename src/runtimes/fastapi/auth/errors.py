"""
FastAPI authentication error responses.

This module provides consistent error responses for authentication failures
in FastAPI applications, following the same patterns as the existing
authentication system.
"""

import logging
from typing import Any
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, model_serializer

from .jwt_validator import JWTValidationError

logger = logging.getLogger(__name__)


class AuthenticationErrorResponse(BaseModel):
    """
    Standardized authentication error response.
    
    This model provides consistent error responses for authentication
    failures across FastAPI endpoints.
    """
    
    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = Field(None, description="Request identifier for tracing")
    
    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serialization for authentication error response.
        
        Handles serialization of datetime objects to ISO format strings
        for consistent JSON output.
        
        Returns:
            Dictionary with properly serialized values
        """
        return {
            "error": self.error,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "request_id": self.request_id,
        }
    



class AuthenticationErrorHandler:
    """
    Handler for authentication errors in FastAPI applications.
    
    This class provides methods to convert authentication errors into
    consistent HTTP responses and handle error logging.
    """
    
    def __init__(self, logger_name: str = "fastapi_auth_errors"):
        """
        Initialize authentication error handler.
        
        Args:
            logger_name: Name for the structured logger
        """
        self.logger = logging.getLogger(logger_name)
    
    def handle_jwt_validation_error(
        self, 
        error: JWTValidationError, 
        request_id: str | None = None
    ) -> HTTPException:
        """
        Handle JWT validation errors.
        
        Args:
            error: JWT validation error
            request_id: Optional request identifier
            
        Returns:
            HTTPException: Formatted HTTP exception
        """
        error_code = getattr(error, 'error_code', 'INVALID_TOKEN')
        
        # Map JWT error codes to HTTP status codes
        status_code_map = {
            'TOKEN_EXPIRED': status.HTTP_401_UNAUTHORIZED,
            'TOKEN_REVOKED': status.HTTP_401_UNAUTHORIZED,
            'INVALID_TOKEN': status.HTTP_401_UNAUTHORIZED,
            'VALIDATION_ERROR': status.HTTP_401_UNAUTHORIZED,
        }
        
        http_status = status_code_map.get(error_code, status.HTTP_401_UNAUTHORIZED)
        
        # Log the error
        self.logger.warning(
            "JWT validation failed",
            extra={
                "error_code": error_code,
                "error_message": str(error),
                "request_id": request_id,
                "http_status": http_status,
            }
        )
        
        # Create error response
        error_response = AuthenticationErrorResponse(
            error=error_code.lower(),
            message=self._get_user_friendly_message(error_code),
            details={
                "error_code": error_code,
                "original_error": str(error),
            },
            request_id=request_id,
        )
        
        return HTTPException(
            status_code=http_status,
            detail=error_response.model_dump()
        )
    
    def handle_authentication_required(
        self, 
        request_id: str | None = None
    ) -> HTTPException:
        """
        Handle authentication required errors.
        
        Args:
            request_id: Optional request identifier
            
        Returns:
            HTTPException: Formatted HTTP exception
        """
        # Log the error
        self.logger.warning(
            "Authentication required",
            extra={
                "error_code": "AUTHENTICATION_REQUIRED",
                "request_id": request_id,
                "http_status": status.HTTP_401_UNAUTHORIZED,
            }
        )
        
        # Create error response
        error_response = AuthenticationErrorResponse(
            error="authentication_required",
            message="Authentication is required to access this resource",
            details={
                "error_code": "AUTHENTICATION_REQUIRED",
                "suggestion": "Please provide a valid authentication token",
            },
            request_id=request_id,
        )
        
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response.model_dump()
        )
    
    def handle_authorization_failed(
        self, 
        required_roles: list[str] | None = None,
        user_roles: list[str] | None = None,
        request_id: str | None = None
    ) -> HTTPException:
        """
        Handle authorization failed errors.
        
        Args:
            required_roles: List of required roles
            user_roles: List of user roles
            request_id: Optional request identifier
            
        Returns:
            HTTPException: Formatted HTTP exception
        """
        # Log the error
        self.logger.warning(
            "Authorization failed",
            extra={
                "error_code": "AUTHORIZATION_FAILED",
                "required_roles": required_roles,
                "user_roles": user_roles,
                "request_id": request_id,
                "http_status": status.HTTP_403_FORBIDDEN,
            }
        )
        
        # Create error response
        error_response = AuthenticationErrorResponse(
            error="authorization_failed",
            message="Insufficient permissions to access this resource",
            details={
                "error_code": "AUTHORIZATION_FAILED",
                "required_roles": required_roles,
                "user_roles": user_roles,
                "suggestion": "Please contact your administrator for access",
            },
            request_id=request_id,
        )
        
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response.model_dump()
        )
    
    def handle_iam_provider_error(
        self, 
        error: Exception, 
        user_id: str | None = None,
        caller_context: str | None = None,
        request_id: str | None = None
    ) -> HTTPException:
        """
        Handle IAM provider errors.
        
        Args:
            error: IAM provider error
            user_id: User identifier
            caller_context: Calling context
            request_id: Optional request identifier
            
        Returns:
            HTTPException: Formatted HTTP exception
        """
        # Log the error
        self.logger.error(
            "IAM provider error",
            extra={
                "error_code": "IAM_PROVIDER_ERROR",
                "error_message": str(error),
                "user_id": user_id,
                "caller_context": caller_context,
                "request_id": request_id,
                "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        )
        
        # Create error response
        error_response = AuthenticationErrorResponse(
            error="iam_provider_error",
            message="Authentication service temporarily unavailable",
            details={
                "error_code": "IAM_PROVIDER_ERROR",
                "original_error": str(error),
                "suggestion": "Please try again later or contact support",
            },
            request_id=request_id,
        )
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )
    
    def handle_unknown_error(
        self, 
        error: Exception, 
        request_id: str | None = None
    ) -> HTTPException:
        """
        Handle unknown authentication errors.
        
        Args:
            error: Unknown error
            request_id: Optional request identifier
            
        Returns:
            HTTPException: Formatted HTTP exception
        """
        # Log the error
        self.logger.error(
            "Unknown authentication error",
            extra={
                "error_code": "UNKNOWN_ERROR",
                "error_message": str(error),
                "error_type": type(error).__name__,
                "request_id": request_id,
                "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        )
        
        # Create error response
        error_response = AuthenticationErrorResponse(
            error="unknown_error",
            message="An unexpected error occurred during authentication",
            details={
                "error_code": "UNKNOWN_ERROR",
                "error_type": type(error).__name__,
                "suggestion": "Please try again or contact support",
            },
            request_id=request_id,
        )
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )
    
    def _get_user_friendly_message(self, error_code: str) -> str:
        """
        Get user-friendly error message for error code.
        
        Args:
            error_code: Error code identifier
            
        Returns:
            User-friendly error message
        """
        messages = {
            'TOKEN_EXPIRED': 'Your authentication token has expired. Please log in again.',
            'TOKEN_REVOKED': 'Your authentication token has been revoked. Please log in again.',
            'INVALID_TOKEN': 'Invalid authentication token. Please check your credentials.',
            'VALIDATION_ERROR': 'Token validation failed. Please try logging in again.',
            'AUTHENTICATION_REQUIRED': 'Authentication is required to access this resource.',
            'AUTHORIZATION_FAILED': 'You do not have permission to access this resource.',
            'IAM_PROVIDER_ERROR': 'Authentication service is temporarily unavailable.',
            'UNKNOWN_ERROR': 'An unexpected error occurred during authentication.',
        }
        
        return messages.get(error_code, 'An authentication error occurred.')
    
    def log_authentication_success(
        self, 
        user_id: str, 
        roles: list[str] | None = None,
        request_id: str | None = None
    ) -> None:
        """
        Log successful authentication.
        
        Args:
            user_id: User identifier
            roles: List of user roles
            request_id: Optional request identifier
        """
        self.logger.info(
            "Authentication successful",
            extra={
                "user_id": user_id,
                "roles": roles,
                "request_id": request_id,
                "event_type": "authentication_success",
            }
        )
    
    def log_authorization_success(
        self, 
        user_id: str, 
        required_roles: list[str] | None = None,
        request_id: str | None = None
    ) -> None:
        """
        Log successful authorization.
        
        Args:
            user_id: User identifier
            required_roles: List of required roles
            request_id: Optional request identifier
        """
        self.logger.info(
            "Authorization successful",
            extra={
                "user_id": user_id,
                "required_roles": required_roles,
                "request_id": request_id,
                "event_type": "authorization_success",
            }
        )


# Global error handler instance (singleton pattern)
_error_handler_instance: AuthenticationErrorHandler | None = None


def get_auth_error_handler() -> AuthenticationErrorHandler:
    """
    Get or create the global authentication error handler instance.
    
    Returns:
        AuthenticationErrorHandler: Global error handler instance
        
    Notes:
        Uses singleton pattern to avoid recreating handler instances
        across requests.
    """
    global _error_handler_instance
    
    if _error_handler_instance is None:
        _error_handler_instance = AuthenticationErrorHandler()
    
    return _error_handler_instance


# Convenience functions for common error scenarios
def raise_authentication_required(request_id: str | None = None) -> None:
    """
    Raise authentication required error.
    
    Args:
        request_id: Optional request identifier
        
    Raises:
        HTTPException: Authentication required error
    """
    handler = get_auth_error_handler()
    raise handler.handle_authentication_required(request_id)


def raise_authorization_failed(
    required_roles: list[str] | None = None,
    user_roles: list[str] | None = None,
    request_id: str | None = None
) -> None:
    """
    Raise authorization failed error.
    
    Args:
        required_roles: List of required roles
        user_roles: List of user roles
        request_id: Optional request identifier
        
    Raises:
        HTTPException: Authorization failed error
    """
    handler = get_auth_error_handler()
    raise handler.handle_authorization_failed(required_roles, user_roles, request_id)


def raise_jwt_validation_error(
    error: JWTValidationError, 
    request_id: str | None = None
) -> None:
    """
    Raise JWT validation error.
    
    Args:
        error: JWT validation error
        request_id: Optional request identifier
        
    Raises:
        HTTPException: JWT validation error
    """
    handler = get_auth_error_handler()
    raise handler.handle_jwt_validation_error(error, request_id)
