"""
Authentication and authorization schemas for client onboarding context.
"""

from .permission_schemas import (
    UserContext,
    PermissionValidationRequest,
    PermissionValidationResponse,
    FormAccessRequest,
    FormAccessResponse,
    AuthorizationError,
    MultiPermissionValidationRequest,
    MultiPermissionValidationResponse,
)

__all__ = [
    "UserContext",
    "PermissionValidationRequest", 
    "PermissionValidationResponse",
    "FormAccessRequest",
    "FormAccessResponse",
    "AuthorizationError",
    "MultiPermissionValidationRequest",
    "MultiPermissionValidationResponse",
] 