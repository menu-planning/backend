"""
Form ownership validation for client onboarding context.

Validates form ownership before webhook configuration and data access.
Follows async patterns and validation standards used in the codebase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field
from src.logging.logger import get_logger

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.services.uow import UnitOfWork


logger = get_logger(__name__)


class FormOwnershipError(Exception):
    """Raised when form ownership validation fails."""


class FormAccessDeniedError(FormOwnershipError):
    """Raised when user lacks access to a form."""


class FormNotFoundError(FormOwnershipError):
    """Raised when form is not found."""


class OwnershipValidationRequest(BaseModel):
    """Request for form ownership validation."""

    user_id: str = Field(..., description="User requesting access")
    form_id: str | None = Field(None, description="TypeForm form ID")
    onboarding_form_id: int | None = Field(
        None, description="Internal onboarding form ID"
    )
    operation: str = Field(..., description="Operation being performed")

    model_config = ConfigDict(frozen=True)


class OwnershipValidationResult(BaseModel):
    """Result of form ownership validation."""

    is_valid: bool = Field(..., description="Whether ownership is valid")
    user_id: str = Field(..., description="Validated user ID")
    form_id: str | None = Field(None, description="TypeForm form ID")
    onboarding_form_id: int | None = Field(None, description="Internal form ID")
    operation: str = Field(..., description="Operation validated")
    reason: str | None = Field(None, description="Reason for validation failure")

    model_config = ConfigDict(frozen=True)


class FormOwnershipValidator:
    """
    Validates form ownership before webhook configuration and data access.

    Ensures users can only access forms they own and prevents unauthorized
    access to form data and configuration.
    """

    def __init__(self) -> None:
        """Initialize the ownership validator."""
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    async def validate_form_access(
        self,
        request: OwnershipValidationRequest,
        uow: UnitOfWork,
    ) -> OwnershipValidationResult:
        """
        Validate user access to a form.

        Args:
            request: Ownership validation request
            uow: Unit of work for database access

        Returns:
            Validation result with ownership status

        Raises:
            FormNotFoundError: If form is not found
            FormAccessDeniedError: If user lacks access
        """
        self._logger.info(
            "Validating form access",
            extra={
                "user_id": request.user_id,
                "form_id": request.form_id,
                "onboarding_form_id": request.onboarding_form_id,
                "operation": request.operation,
            },
        )

        # Validate by internal onboarding form ID
        if request.onboarding_form_id is not None:
            return await self._validate_by_onboarding_form_id(request, uow)

        # Validate by TypeForm form ID
        if request.form_id is not None:
            return await self._validate_by_typeform_id(request, uow)

        # No form identifier provided
        return OwnershipValidationResult(
            is_valid=False,
            user_id=request.user_id,
            form_id=None,
            onboarding_form_id=None,
            operation=request.operation,
            reason="No form identifier provided",
        )

    async def validate_webhook_access(
        self,
        typeform_id: str,
        user_id: str,
        uow: UnitOfWork,
    ) -> OwnershipValidationResult:
        """
        Validate webhook access for TypeForm form.

        Args:
            typeform_id: TypeForm form ID
            user_id: User requesting access
            uow: Unit of work for database access

        Returns:
            Validation result with ownership status
        """
        request = OwnershipValidationRequest(
            user_id=user_id,
            form_id=typeform_id,
            onboarding_form_id=None,
            operation="webhook_access",
        )

        return await self.validate_form_access(request, uow)

    async def validate_response_access(
        self,
        onboarding_form_id: int,
        user_id: str,
        uow: UnitOfWork,
    ) -> OwnershipValidationResult:
        """
        Validate access to form responses.

        Args:
            onboarding_form_id: Internal onboarding form ID
            user_id: User requesting access
            uow: Unit of work for database access

        Returns:
            Validation result with ownership status
        """
        request = OwnershipValidationRequest(
            user_id=user_id,
            form_id=None,
            onboarding_form_id=onboarding_form_id,
            operation="response_access",
        )

        return await self.validate_form_access(request, uow)

    async def _validate_by_onboarding_form_id(
        self,
        request: OwnershipValidationRequest,
        uow: UnitOfWork,
    ) -> OwnershipValidationResult:
        """Validate ownership by internal onboarding form ID."""
        # Type guard to ensure onboarding_form_id is not None
        if request.onboarding_form_id is None:
            error_msg = "onboarding_form_id is required for this validation"
            raise ValueError(error_msg)

        async with uow:
            # Get onboarding form
            onboarding_form = await uow.onboarding_forms.get_by_id(
                request.onboarding_form_id
            )

            if not onboarding_form:
                self._logger.warning(
                    "Onboarding form not found",
                    extra={
                        "onboarding_form_id": request.onboarding_form_id,
                        "user_id": request.user_id,
                    },
                )
                error_msg = f"Onboarding form {request.onboarding_form_id} not found"
                raise FormNotFoundError(error_msg)

            # Check ownership
            if onboarding_form.user_id != request.user_id:
                self._logger.warning(
                    "Form access denied - ownership mismatch",
                    extra={
                        "onboarding_form_id": request.onboarding_form_id,
                        "requested_user_id": request.user_id,
                        "actual_owner_id": onboarding_form.user_id,
                        "operation": request.operation,
                    },
                )
                error_msg = (
                    f"User {request.user_id} does not own form "
                    f"{request.onboarding_form_id}"
                )
                raise FormAccessDeniedError(error_msg)

            self._logger.info(
                "Form ownership validated successfully",
                extra={
                    "onboarding_form_id": request.onboarding_form_id,
                    "user_id": request.user_id,
                    "operation": request.operation,
                },
            )

            return OwnershipValidationResult(
                is_valid=True,
                user_id=request.user_id,
                form_id=onboarding_form.typeform_id,
                onboarding_form_id=request.onboarding_form_id,
                operation=request.operation,
                reason=None,
            )

    async def _validate_by_typeform_id(
        self,
        request: OwnershipValidationRequest,
        uow: UnitOfWork,
    ) -> OwnershipValidationResult:
        """Validate ownership by TypeForm form ID."""
        # Type guard to ensure form_id is not None
        if request.form_id is None:
            error_msg = "form_id is required for this validation"
            raise ValueError(error_msg)

        async with uow:
            # Get onboarding form by TypeForm ID
            onboarding_form = await uow.onboarding_forms.get_by_typeform_id(
                request.form_id
            )

            if not onboarding_form:
                self._logger.warning(
                    "Form not found by TypeForm ID",
                    extra={
                        "typeform_id": request.form_id,
                        "user_id": request.user_id,
                    },
                )
                error_msg = f"Form with TypeForm ID {request.form_id} not found"
                raise FormNotFoundError(error_msg)

            # Check ownership
            if onboarding_form.user_id != request.user_id:
                self._logger.warning(
                    "Form access denied - ownership mismatch via TypeForm ID",
                    extra={
                        "typeform_id": request.form_id,
                        "onboarding_form_id": onboarding_form.id,
                        "requested_user_id": request.user_id,
                        "actual_owner_id": onboarding_form.user_id,
                        "operation": request.operation,
                    },
                )
                error_msg = (
                    f"User {request.user_id} does not own form {request.form_id}"
                )
                raise FormAccessDeniedError(error_msg)

            self._logger.info(
                "Form ownership validated successfully via TypeForm ID",
                extra={
                    "typeform_id": request.form_id,
                    "onboarding_form_id": onboarding_form.id,
                    "user_id": request.user_id,
                    "operation": request.operation,
                },
            )

            return OwnershipValidationResult(
                is_valid=True,
                user_id=request.user_id,
                form_id=request.form_id,
                onboarding_form_id=onboarding_form.id,
                operation=request.operation,
                reason=None,
            )
