"""
Auth middleware for client onboarding context.

This middleware provides specialized authentication and authorization for client
onboarding features by extending the shared_kernel auth patterns with form
ownership validation.

Features:
- Integration with UnifiedIAMProvider from shared_kernel
- Form ownership validation for secure access control
- Client onboarding context-specific permissions
- User-scoped form access validation
- Integration with existing auth patterns
"""

import json
from contextlib import asynccontextmanager
from typing import Any

from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.contexts.shared_kernel.middleware.auth_middleware import (
    AuthContext,
    AuthorizationError,
)
from src.contexts.shared_kernel.middleware.auth_middleware import (
    AuthMiddleware as SharedAuthMiddleware,
)
from src.logging.logger import correlation_id_ctx

# Constants
HTTP_OK_STATUS = 200
NO_AUTH_CONTEXT_MSG = "No authentication context available"


class ClientOnboardingAuthContext(AuthContext):
    """
    Extended auth context for client onboarding with form ownership validation.

    Extends the shared_kernel AuthContext with client onboarding-specific
    permission checking and form ownership validation.
    """

    def __init__(self, user_id: str, user_object: Any, *, is_authenticated: bool):
        super().__init__(
            user_id=user_id,
            user_object=user_object,
            is_authenticated=is_authenticated,
            caller_context="client_onboarding",
        )

    def can_access_form(self, form_owner_id: str) -> bool:
        """Check if user can access a form (owner or has form management permission)."""
        if not self.is_authenticated:
            return False

        return self.user_id == form_owner_id or self.has_permission(
            "client_onboarding:form:read_all"
        )

    def can_manage_form(self, form_owner_id: str) -> bool:
        """Check if user can manage a form (owner or has form management permission)."""
        if not self.is_authenticated:
            return False

        return self.user_id == form_owner_id or self.has_permission(
            "client_onboarding:form:manage_all"
        )

    def can_configure_webhooks(self, form_owner_id: str) -> bool:
        """Check if user can configure webhooks for a form."""
        if not self.is_authenticated:
            return False

        return self.user_id == form_owner_id or self.has_permission(
            "client_onboarding:webhook:configure"
        )

    def can_view_responses(self, form_owner_id: str) -> bool:
        """Check if user can view form responses."""
        if not self.is_authenticated:
            return False

        return self.user_id == form_owner_id or self.has_permission(
            "client_onboarding:response:read_all"
        )


class ClientOnboardingAuthMiddleware(SharedAuthMiddleware):
    """
    Client onboarding-specific auth middleware.

    Extends the shared_kernel AuthMiddleware with client onboarding context
    and specialized form ownership validation capabilities.
    """

    def __init__(
        self,
        *,
        require_authentication: bool = True,
        logger_name: str = "client_onboarding_auth",
    ):
        """
        Initialize client onboarding auth middleware.

        Args:
            require_authentication: Whether to require authentication for all requests
            logger_name: Name for auth logger instance
        """
        super().__init__(
            caller_context="client_onboarding",
            require_authentication=require_authentication,
            logger_name=logger_name,
        )

    async def _authenticate_user(
        self, event: dict[str, Any]
    ) -> ClientOnboardingAuthContext:
        """
        Authenticate user and create client onboarding auth context.

        Args:
            event: AWS Lambda event dictionary

        Returns:
            ClientOnboardingAuthContext with user info and permissions

        Raises:
            AuthenticationError: When authentication fails
        """
        correlation_id = correlation_id_ctx.get() or "unknown"

        try:
            # Extract user ID from event using LambdaHelpers
            user_id = LambdaHelpers.extract_user_id(event)

            if not user_id:
                self.structured_logger.warning(
                    "No user ID found in event",
                    correlation_id=correlation_id,
                    event_path_params=event.get("pathParameters"),
                    event_headers=(
                        list(event.get("headers", {}).keys())
                        if event.get("headers")
                        else []
                    ),
                )
                return ClientOnboardingAuthContext(
                    user_id="", user_object=None, is_authenticated=False
                )

            # Get user data from IAM provider
            iam_response = await self.iam_provider.get_user(
                user_id, "client_onboarding"
            )

            if iam_response.get("statusCode") == HTTP_OK_STATUS:
                user_data = json.loads(iam_response["body"])

                self.structured_logger.debug(
                    "User authenticated successfully",
                    correlation_id=correlation_id,
                    user_id=user_id,
                    caller_context="client_onboarding",
                )

                return ClientOnboardingAuthContext(
                    user_id=user_id, user_object=user_data, is_authenticated=True
                )
            self.structured_logger.warning(
                "IAM authentication failed",
                correlation_id=correlation_id,
                user_id=user_id,
                iam_status_code=iam_response.get("statusCode"),
                caller_context="client_onboarding",
            )

            return ClientOnboardingAuthContext(
                user_id=user_id, user_object=None, is_authenticated=False
            )

        except Exception as e:
            self.structured_logger.exception(
                "Authentication error",
                correlation_id=correlation_id,
                error=str(e),
                caller_context="client_onboarding",
            )

            return ClientOnboardingAuthContext(
                user_id="", user_object=None, is_authenticated=False
            )

    def get_current_auth_context(self) -> ClientOnboardingAuthContext | None:
        """Get the current authentication context for this request."""
        # Cast the base auth context to our specialized type
        if isinstance(self._current_auth_context, ClientOnboardingAuthContext):
            return self._current_auth_context
        return None

    async def require_form_ownership(self, form_owner_id: str) -> None:
        """
        Require that the current user owns the specified form or has management
        permissions.

        Args:
            form_owner_id: The user ID that owns the form

        Raises:
            AuthorizationError: When user lacks required permissions
        """
        auth_context = self.get_current_auth_context()
        if not auth_context:
            raise AuthorizationError(NO_AUTH_CONTEXT_MSG)

        if not auth_context.can_manage_form(form_owner_id):
            correlation_id = correlation_id_ctx.get() or "unknown"
            self.structured_logger.warning(
                "Form ownership authorization failed",
                correlation_id=correlation_id,
                user_id=auth_context.user_id,
                form_owner_id=form_owner_id,
                caller_context="client_onboarding",
            )

            error_msg = (
                f"User does not have permission to manage form owned by "
                f"{form_owner_id}"
            )
            raise AuthorizationError(error_msg)

    async def require_form_access(self, form_owner_id: str) -> None:
        """
        Require that the current user can access the specified form.

        Args:
            form_owner_id: The user ID that owns the form

        Raises:
            AuthorizationError: When user lacks required permissions
        """
        auth_context = self.get_current_auth_context()
        if not auth_context:
            raise AuthorizationError(NO_AUTH_CONTEXT_MSG)

        if not auth_context.can_access_form(form_owner_id):
            correlation_id = correlation_id_ctx.get() or "unknown"
            self.structured_logger.warning(
                "Form access authorization failed",
                correlation_id=correlation_id,
                user_id=auth_context.user_id,
                form_owner_id=form_owner_id,
                caller_context="client_onboarding",
            )

            error_msg = (
                f"User does not have permission to access form owned by "
                f"{form_owner_id}"
            )
            raise AuthorizationError(error_msg)

    @asynccontextmanager
    async def with_form_ownership_check(self, form_owner_id: str):
        """
        Context manager for form ownership validation.

        Args:
            form_owner_id: The user ID that owns the form

        Raises:
            AuthorizationError: When user lacks required permissions
        """
        await self.require_form_ownership(form_owner_id)
        try:
            yield self.get_current_auth_context()
        finally:
            # Cleanup if needed
            pass

    @asynccontextmanager
    async def with_form_access_check(self, form_owner_id: str):
        """
        Context manager for form access validation.

        Args:
            form_owner_id: The user ID that owns the form

        Raises:
            AuthorizationError: When user lacks required permissions
        """
        await self.require_form_access(form_owner_id)
        try:
            yield self.get_current_auth_context()
        finally:
            # Cleanup if needed
            pass


# Convenience function to create client onboarding auth middleware
def create_client_onboarding_auth_middleware(
    *,
    require_authentication: bool = True,
) -> ClientOnboardingAuthMiddleware:
    """
    Create a client onboarding auth middleware instance.

    Args:
        require_authentication: Whether to require authentication for all requests

    Returns:
        Configured ClientOnboardingAuthMiddleware instance
    """
    return ClientOnboardingAuthMiddleware(require_authentication=require_authentication)
