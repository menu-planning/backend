"""
Permission validation schemas for client onboarding context.

Pydantic models for validating permissions, user context, and access control
following the established patterns in the codebase.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field
from src.contexts.client_onboarding.core.domain.enums import (
    Permission as ClientOnboardingPermission,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    MODEL_CONFIG,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_permissions_collection,
)


class UserContext(BaseModel):
    """
    User context for permission validation.

    Contains user information needed for access control validation
    in the client onboarding context.
    """

    model_config = MODEL_CONFIG

    user_id: str = Field(..., description="User ID for permission validation", gt=0)
    permissions: Annotated[
        frozenset[str],
        BeforeValidator(
            lambda v: validate_permissions_collection(
                v,
                allowed_permissions={perm.value for perm in ClientOnboardingPermission},
            )
        ),
        Field(
            default_factory=frozenset,
            description="Permissions associated with the user",
        ),
    ]
    roles: frozenset[str] = Field(
        default_factory=frozenset,
        description="Roles associated with the user in client onboarding context",
    )
    context: str = Field(
        default="client_onboarding",
        description="Context identifier for the permission validation",
    )


class PermissionValidationRequest(BaseModel):
    """
    Request schema for permission validation.

    Used to validate if a user has the required permissions
    to perform a specific operation.
    """

    model_config = MODEL_CONFIG

    user_context: UserContext = Field(..., description="User context for validation")
    required_permission: str = Field(
        ..., description="Permission required to perform the operation"
    )
    operation: str = Field(..., description="Operation being validated")
    resource_context: dict[str, Any] | None = Field(
        default=None, description="Additional context about the resource being accessed"
    )


class PermissionValidationResponse(BaseModel):
    """
    Response schema for permission validation.

    Contains the result of permission validation with details
    about the validation outcome.
    """

    model_config = MODEL_CONFIG

    is_valid: bool = Field(..., description="Whether the permission validation passed")
    user_id: str = Field(..., description="User ID that was validated")
    required_permission: str = Field(..., description="Permission that was required")
    operation: str = Field(..., description="Operation that was validated")
    reason: str | None = Field(
        default=None, description="Reason for validation failure (if applicable)"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Additional context about the validation result"
    )


class FormAccessRequest(BaseModel):
    """
    Request schema for form access validation.

    Used to validate access to specific onboarding forms
    with ownership and permission checks.
    """

    model_config = MODEL_CONFIG

    user_context: UserContext = Field(..., description="User context for validation")
    form_id: str | None = Field(
        default=None, description="TypeForm form ID (external identifier)"
    )
    onboarding_form_id: int | None = Field(
        default=None, description="Internal onboarding form ID", gt=0
    )
    access_type: str = Field(
        ..., description="Type of access requested (read, write, configure, delete)"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure at least one form identifier is provided
        if not self.form_id and not self.onboarding_form_id:
            error_msg = "Either form_id or onboarding_form_id must be provided"
            raise ValueError(error_msg)


class FormAccessResponse(BaseModel):
    """
    Response schema for form access validation.

    Contains the result of form access validation with ownership
    and permission information.
    """

    model_config = MODEL_CONFIG

    is_valid: bool = Field(..., description="Whether access is granted")
    user_id: str = Field(..., description="User ID that was validated")
    form_id: str | None = Field(
        default=None, description="TypeForm form ID that was accessed"
    )
    onboarding_form_id: int | None = Field(
        default=None, description="Internal onboarding form ID that was accessed"
    )
    access_type: str = Field(..., description="Type of access that was validated")
    is_owner: bool = Field(..., description="Whether the user owns the form")
    has_permission: bool = Field(
        ..., description="Whether the user has required permission"
    )
    reason: str | None = Field(
        default=None, description="Reason for access denial (if applicable)"
    )


class AuthorizationError(BaseModel):
    """
    Schema for authorization error responses.

    Standardized error response for authorization failures
    in the client onboarding context.
    """

    model_config = MODEL_CONFIG

    error_type: str = Field(
        default="authorization_error", description="Type of authorization error"
    )
    message: str = Field(..., description="Human-readable error message")
    user_id: str = Field(..., description="User ID that failed authorization")
    required_permission: str | None = Field(
        default=None, description="Permission that was required but missing"
    )
    operation: str = Field(..., description="Operation that was denied")
    context: dict[str, Any] | None = Field(
        default=None, description="Additional context about the authorization failure"
    )


class MultiPermissionValidationRequest(BaseModel):
    """
    Request schema for validating multiple permissions at once.

    Used when an operation requires multiple permissions
    or when batch validation is needed.
    """

    model_config = MODEL_CONFIG

    user_context: UserContext = Field(..., description="User context for validation")
    required_permissions: list[str] = Field(
        ..., description="List of permissions required for the operation", min_length=1
    )
    operation: str = Field(..., description="Operation being validated")
    require_all: bool = Field(
        default=True,
        description="Whether all permissions are required (AND) or any permission (OR)",
    )
    resource_context: dict[str, Any] | None = Field(
        default=None, description="Additional context about the resource being accessed"
    )


class MultiPermissionValidationResponse(BaseModel):
    """
    Response schema for multiple permission validation.

    Contains detailed results for each permission validation
    along with the overall result.
    """

    model_config = MODEL_CONFIG

    is_valid: bool = Field(..., description="Whether the overall validation passed")
    user_id: str = Field(..., description="User ID that was validated")
    operation: str = Field(..., description="Operation that was validated")
    required_permissions: list[str] = Field(
        ..., description="Permissions that were required"
    )
    granted_permissions: list[str] = Field(
        ..., description="Permissions that the user has"
    )
    missing_permissions: list[str] = Field(
        ..., description="Permissions that the user lacks"
    )
    require_all: bool = Field(..., description="Whether all permissions were required")
    validation_details: dict[str, bool] = Field(
        ..., description="Detailed validation result for each permission"
    )
    reason: str | None = Field(
        default=None, description="Reason for validation failure (if applicable)"
    )
