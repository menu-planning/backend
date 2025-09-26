from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

# Re-export of the existing implementation to the new location.
# The content is moved verbatim from services/webhook_manager.py to maintain behavior.
from src.logging.logger import get_logger

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.services.uow import UnitOfWork

from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
    OnboardingFormStatus,
)
from src.contexts.client_onboarding.core.services.exceptions import (
    FormOwnershipError,
    TypeFormAPIError,
    TypeFormAuthenticationError,
    TypeFormFormNotFoundError,
    TypeFormWebhookNotFoundError,
    WebhookConfigurationError,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.client import (
    FormInfo,
    TypeFormClient,
    WebhookInfo,
    create_typeform_client,
)

logger = get_logger(__name__)


@dataclass
class WebhookStatusInfo:
    """Webhook status information for monitoring and diagnostics.

    Attributes:
        onboarding_form_id: Database onboarding form identifier.
        typeform_id: TypeForm form identifier.
        webhook_exists: Whether webhook exists in TypeForm.
        webhook_info: TypeForm webhook information if exists.
        database_status: Current database status of the form.
        database_webhook_url: Webhook URL stored in database.
        status_synchronized: Whether database and TypeForm status match.
        last_checked: Timestamp of last status check.
        issues: List of identified issues or discrepancies.
    """
    onboarding_form_id: int
    typeform_id: str
    webhook_exists: bool
    webhook_info: WebhookInfo | None
    database_status: str
    database_webhook_url: str | None
    status_synchronized: bool
    last_checked: datetime
    issues: list[str]


@dataclass
class WebhookOperationRecord:
    """Record of webhook operation for auditing and tracking.

    Attributes:
        operation: Type of operation performed ('create', 'update', 'delete', 'enable', 'disable').
        onboarding_form_id: Database onboarding form identifier.
        typeform_id: TypeForm form identifier.
        webhook_url: Webhook URL involved in the operation.
        success: Whether the operation was successful.
        error_message: Error message if operation failed.
        timestamp: When the operation occurred.
        webhook_id: TypeForm webhook identifier if applicable.
    """
    operation: str  # 'create', 'update', 'delete', 'enable', 'disable'
    onboarding_form_id: int
    typeform_id: str
    webhook_url: str | None
    success: bool
    error_message: str | None
    timestamp: datetime
    webhook_id: str | None = None


class WebhookManager:
    """Webhook manager for TypeForm webhook lifecycle operations.

    Manages the complete lifecycle of TypeForm webhooks including creation,
    updates, deletion, and status synchronization with database records.
    Provides comprehensive webhook management with error handling and auditing.
    """

    def __init__(self, typeform_client: TypeFormClient | None = None):
        self.typeform_client = typeform_client or create_typeform_client()
        self.webhook_tag = "client_onboarding"

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        if hasattr(self.typeform_client, "close"):
            await self.typeform_client.close()

    async def setup_onboarding_form_webhook(
        self,
        uow: UnitOfWork,
        user_id: str,
        typeform_id: str,
        webhook_url: str | None = None,
        validate_ownership: bool = True,
    ) -> tuple[OnboardingForm, WebhookInfo]:
        """Set up onboarding form webhook with validation and database persistence.

        Args:
            uow: Unit of work for database operations.
            user_id: User identifier for form ownership.
            typeform_id: TypeForm form identifier.
            webhook_url: Optional webhook URL override.
            validate_ownership: Whether to validate TypeForm access.

        Returns:
            Tuple of (OnboardingForm, WebhookInfo) on success.

        Raises:
            TypeFormAPIError: For TypeForm API access or validation failures.
            WebhookConfigurationError: For webhook setup failures.
            ValueError: For invalid form configuration or ownership issues.
        """
        logger.info(
            "Setting up onboarding form webhook",
            user_id=user_id,
            typeform_id=typeform_id,
            action="webhook_setup_start"
        )
        if validate_ownership:
            try:
                form_info = await self.typeform_client.get_form(typeform_id)
                logger.info("TypeForm access validated", form_title=form_info.title, action="typeform_validation_success")
            except TypeFormFormNotFoundError:
                # True 404 from Typeform
                logger.warning(
                    "TypeForm form not found or inaccessible",
                    action="typeform_validation_error",
                    typeform_id=typeform_id,
                    error_type="FormNotFound"
                )
                raise
            except TypeFormAuthenticationError as e:
                # Auth/permission problems - bubble up as-is
                logger.error(
                    "TypeForm authentication failed",
                    action="typeform_auth_failure",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    typeform_id=typeform_id,
                    resolution_hint="Check TypeForm API credentials and permissions",
                    exc_info=True
                )
                raise
            except TypeFormAPIError as e:
                # API-level error surfaced from client - re-raise for accurate handling
                logger.error(
                    "TypeForm API validation error",
                    action="typeform_api_error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    typeform_id=typeform_id,
                    resolution_hint="Verify TypeForm API request format and parameters",
                    exc_info=True
                )
                raise
            except Exception as e:
                # Network/connectivity or unexpected error - don't mask as 404
                logger.error(
                    "Network or unexpected error contacting TypeForm",
                    action="typeform_network_error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    typeform_id=typeform_id,
                    resolution_hint="Check network connectivity and TypeForm service status",
                    exc_info=True
                )
                raise TypeFormAPIError(
                    message="Network error while contacting TypeForm",
                    status_code=503,
                    response_data={"detail": str(e)},
                ) from e

        webhook_url = webhook_url or config.webhook_endpoint_url
        if not webhook_url:
            raise ValueError("Webhook URL must be provided or configured")

        try:
            async with uow:
                existing_form = await uow.onboarding_forms.get_by_typeform_id(
                    typeform_id
                )
            if existing_form and str(existing_form.user_id) != str(user_id):
                raise ValueError(
                    f"TypeForm {typeform_id} is already associated with another user"
                )

            if existing_form:
                logger.info(
                    "Form already exists for user",
                    typeform_id=typeform_id,
                    user_id_suffix=user_id[-4:] if len(user_id) >= 4 else user_id,  # Last 4 chars for debugging
                    action="form_exists_check",
                    business_context="webhook_management"
                )
                try:
                    webhook_info = await self.typeform_client.get_webhook(
                        typeform_id, self.webhook_tag
                    )
                    existing_form.webhook_url = webhook_url
                    await uow.commit()
                except (TypeFormWebhookNotFoundError, TypeFormFormNotFoundError):
                    logger.info(
                        "Webhook not found for existing form, creating",
                        typeform_id=typeform_id,
                        action="webhook_create_for_existing"
                    )
                else:
                    return existing_form, webhook_info

            if not existing_form:
                onboarding_form = await self._create_onboarding_form_record(
                    uow, user_id, typeform_id, webhook_url
                )
            else:
                onboarding_form = existing_form
                onboarding_form.webhook_url = webhook_url

            webhook_info = await self._setup_typeform_webhook(typeform_id, webhook_url)
            await uow.commit()

            await self.track_webhook_operation(
                operation="setup_webhook",
                onboarding_form_id=onboarding_form.id,
                typeform_id=typeform_id,
                success=True,
                webhook_url=webhook_url,
                details={
                    "webhook_id": webhook_info.id,
                    "webhook_tag": webhook_info.tag,
                },
            )

            logger.info(
                "Successfully set up onboarding form webhook",
                onboarding_form_id=onboarding_form.id,
                action="webhook_setup_success"
            )

        except Exception as e:
            logger.error(
                "Failed to set up onboarding form webhook",
                action="webhook_setup_failure",
                error_type=type(e).__name__,
                error_message=str(e),
                user_id=user_id,
                typeform_id=typeform_id,
                resolution_hint="Check TypeForm API connectivity and webhook configuration",
                exc_info=True
            )
            await uow.rollback()
            onboarding_form_id = (
                existing_form.id if "existing_form" in locals() and existing_form else 0
            )
            await self.track_webhook_operation(
                operation="setup_webhook",
                onboarding_form_id=onboarding_form_id,
                typeform_id=typeform_id,
                success=False,
                error_message=str(e),
                webhook_url=webhook_url,
            )
            raise
        else:
            return onboarding_form, webhook_info

    async def update_webhook_url(
        self, uow: UnitOfWork, onboarding_form_id: int, new_webhook_url: str
    ) -> WebhookInfo:
        """Update webhook URL for an existing onboarding form.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.
            new_webhook_url: New webhook URL to set.

        Returns:
            Updated WebhookInfo from TypeForm.

        Raises:
            WebhookConfigurationError: If form not found or webhook update fails.
        """
        logger.info("Updating webhook URL", onboarding_form_id=onboarding_form_id, action="webhook_url_update_start")
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            try:
                webhook_info = await self.typeform_client.update_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                    webhook_url=new_webhook_url,
                )
                onboarding_form.webhook_url = new_webhook_url
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                await self.track_webhook_operation(
                    operation="update",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=new_webhook_url,
                    webhook_id=webhook_info.id,
                )
                logger.info(
                    "Updated webhook URL for form",
                    onboarding_form_id=onboarding_form_id,
                    new_webhook_url=new_webhook_url,
                    action="webhook_url_update_success"
                )
                return webhook_info
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="update",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=(
                        onboarding_form.typeform_id
                        if "onboarding_form" in locals()
                        else "unknown"
                    ),
                    success=False,
                    webhook_url=new_webhook_url,
                    error_message=str(e),
                )
                logger.error(
                    "Failed to update webhook URL",
                    action="webhook_url_update_failure",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    onboarding_form_id=onboarding_form_id,
                    new_webhook_url=new_webhook_url,
                    resolution_hint="Verify webhook configuration and URL format is valid",
                    exc_info=True
                )
                raise

    async def disable_webhook(self, uow_factory: Callable[[],UnitOfWork], onboarding_form_id: int) -> bool:
        """Disable webhook for an onboarding form.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.

        Returns:
            True if webhook was disabled successfully.

        Raises:
            WebhookConfigurationError: If form not found or webhook disable fails.
        """
        logger.info("Disabling webhook", onboarding_form_id=onboarding_form_id, action="webhook_disable_start")
        async with uow_factory() as uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            try:
                _ = await self.typeform_client.update_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                    enabled=False,
                )
                onboarding_form.status = OnboardingFormStatus.PAUSED
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                await self.track_webhook_operation(
                    operation="disable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url,
                )
                logger.info(
                    "Disabled webhook for onboarding form",
                    onboarding_form_id=onboarding_form_id,
                    action="webhook_disable_success"
                )
                return True
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="disable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=(
                        onboarding_form.typeform_id
                        if "onboarding_form" in locals()
                        else "unknown"
                    ),
                    success=False,
                    error_message=str(e),
                )
                logger.error(
                    "Failed to disable webhook",
                    action="webhook_disable_failure",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    onboarding_form_id=onboarding_form_id,
                    resolution_hint="Check webhook exists and TypeForm API permissions",
                    exc_info=True
                )
                raise

    async def enable_webhook(self, uow_factory: Callable[[],UnitOfWork], onboarding_form_id: int) -> bool:
        """Enable webhook for an onboarding form.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.

        Returns:
            True if webhook was enabled successfully.

        Raises:
            WebhookConfigurationError: If form not found or webhook enable fails.
        """
        logger.info("Enabling webhook", onboarding_form_id=onboarding_form_id, action="webhook_enable_start")
        async with uow_factory() as uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            try:
                _ = await self.typeform_client.update_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                    enabled=True,
                )
                onboarding_form.status = OnboardingFormStatus.ACTIVE
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                await self.track_webhook_operation(
                    operation="enable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url,
                )
                logger.info(
                    "Enabled webhook for onboarding form",
                    onboarding_form_id=onboarding_form_id,
                    action="webhook_enable_success"
                )
                return True
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="enable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=(
                        onboarding_form.typeform_id
                        if "onboarding_form" in locals()
                        else "unknown"
                    ),
                    success=False,
                    error_message=str(e),
                )
                logger.error(
                    "Failed to enable webhook",
                    action="webhook_enable_failure",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    onboarding_form_id=onboarding_form_id,
                    resolution_hint="Verify webhook configuration and TypeForm API status",
                    exc_info=True
                )
                raise

    async def delete_webhook_configuration(
        self, uow: UnitOfWork, onboarding_form_id: int
    ) -> bool:
        """Delete webhook configuration for an onboarding form.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.

        Returns:
            True if webhook configuration was deleted successfully.

        Raises:
            WebhookConfigurationError: If form not found or webhook deletion fails.
        """
        logger.info(
            "Deleting webhook configuration for onboarding form",
            onboarding_form_id=onboarding_form_id,
            action="webhook_config_delete_start"
        )
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            try:
                await self.typeform_client.delete_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                )
                onboarding_form.status = OnboardingFormStatus.DELETED
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url,
                )
                logger.info(
                    "Deleted webhook configuration for onboarding form",
                    onboarding_form_id=onboarding_form_id,
                    action="webhook_config_delete_success"
                )
                return True
            except TypeFormFormNotFoundError:
                onboarding_form.status = OnboardingFormStatus.DELETED
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url,
                    error_message="Webhook already deleted in TypeForm",
                )
                logger.info(
                    "Webhook already deleted, updated database status",
                    onboarding_form_id=onboarding_form_id,
                    action="webhook_already_deleted"
                )
                return True
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=(
                        onboarding_form.typeform_id
                        if "onboarding_form" in locals()
                        else "unknown"
                    ),
                    success=False,
                    error_message=str(e),
                )
                logger.error(
                    "Failed to delete webhook configuration",
                    action="webhook_config_delete_failure",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    onboarding_form_id=onboarding_form_id,
                    resolution_hint="Check database connectivity and webhook record existence",
                    exc_info=True
                )
                raise

    async def get_webhook_status(
        self, uow_factory: Callable[[],UnitOfWork], onboarding_form_id: int
    ) -> WebhookInfo | None:
        """Get webhook status for an onboarding form.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.

        Returns:
            WebhookInfo if webhook exists, None otherwise.

        Raises:
            WebhookConfigurationError: If form not found.
        """
        async with uow_factory() as uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            try:
                webhook_info = await self.typeform_client.get_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                )
                return webhook_info
            except TypeFormFormNotFoundError:
                logger.warning(
                    "Webhook not found for onboarding form",
                    onboarding_form_id=onboarding_form_id,
                    action="webhook_not_found"
                )
                return None

    async def list_user_onboarding_forms(
        self, uow_factory: Callable[[],UnitOfWork], user_id: str
    ) -> list[OnboardingForm]:
        """List all onboarding forms for a user.

        Args:
            uow: Unit of work for database operations.
            user_id: User identifier.

        Returns:
            List of OnboardingForm objects for the user.
        """
        async with uow_factory() as uow:
            return await uow.onboarding_forms.get_by_user_id(user_id)

    async def get_comprehensive_webhook_status(
        self, uow_factory: Callable[[],UnitOfWork], onboarding_form_id: int
    ) -> WebhookStatusInfo:
        """Get comprehensive webhook status with synchronization analysis.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.

        Returns:
            WebhookStatusInfo with comprehensive status and issue analysis.

        Raises:
            WebhookConfigurationError: If form not found.
        """
        logger.info(
            "Getting comprehensive webhook status for form",
            onboarding_form_id=onboarding_form_id,
            action="webhook_status_comprehensive_start"
        )
        async with uow_factory() as uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            issues: list[str] = []
            webhook_info: WebhookInfo | None = None
            webhook_exists = False
            try:
                webhook_info = await self.typeform_client.get_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                )
                webhook_exists = True
                logger.info("Webhook found", webhook_id=webhook_info.id, action="webhook_found", business_context="webhook_management")
            except TypeFormFormNotFoundError:
                logger.info(
                    "No webhook found for form",
                    typeform_id=onboarding_form.typeform_id,
                    action="webhook_not_found",
                    business_context="webhook_management"
                )
                webhook_exists = False
            except Exception as e:
                issues.append(f"Error checking webhook status: {e}")
                logger.warning(
                    "Error checking webhook status",
                    action="webhook_status_check_error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                    resolution_hint="Verify TypeForm API connectivity and webhook configuration"
                )

            status_synchronized = self._check_status_synchronization(
                onboarding_form, webhook_info, webhook_exists
            )
            if not status_synchronized:
                issues.append("Database and TypeForm webhook status not synchronized")

            if webhook_exists and webhook_info and onboarding_form.webhook_url and webhook_info.url != onboarding_form.webhook_url:
                    issues.append(
                        f"Webhook URL mismatch: DB={onboarding_form.webhook_url}, TypeForm={webhook_info.url}"
                    )

            return WebhookStatusInfo(
                onboarding_form_id=onboarding_form_id,
                typeform_id=onboarding_form.typeform_id,
                webhook_exists=webhook_exists,
                webhook_info=webhook_info,
                database_status=onboarding_form.status.value,
                database_webhook_url=onboarding_form.webhook_url,
                status_synchronized=status_synchronized,
                last_checked=datetime.now(),
                issues=issues,
            )

    async def bulk_webhook_status_check(
        self, uow_factory: Callable[[],UnitOfWork], user_id: str, include_deleted: bool = False
    ) -> list[WebhookStatusInfo]:
        """Perform bulk webhook status check for all user forms.

        Args:
            uow: Unit of work for database operations.
            user_id: User identifier.
            include_deleted: Whether to include deleted forms in the check.

        Returns:
            List of WebhookStatusInfo objects for all user forms.
        """
        logger.info(
            "Performing bulk webhook status check",
            user_id=user_id,
            include_deleted=include_deleted,
            action="bulk_webhook_status_start"
        )
        async with uow_factory() as uow:
            forms = await uow.onboarding_forms.get_by_user_id(user_id)
            if not include_deleted:
                forms = [f for f in forms if f.status != OnboardingFormStatus.DELETED]
            logger.info(
                "Checking onboarding forms",
                form_count=len(forms),
                user_id_suffix=user_id[-4:] if len(user_id) >= 4 else user_id,  # Last 4 chars for debugging
                action="forms_check_start",
                business_context="webhook_management"
            )
            status_results: list[WebhookStatusInfo] = []
            for form in forms:
                try:
                    status_info = await self.get_comprehensive_webhook_status(
                        uow_factory, form.id
                    )
                    status_results.append(status_info)
                except Exception as e:
                    logger.error("Error checking form status", form_id=form.id, error=str(e), action="form_status_check_error")
                    error_status = WebhookStatusInfo(
                        onboarding_form_id=form.id,
                        typeform_id=form.typeform_id,
                        webhook_exists=False,
                        webhook_info=None,
                        database_status=form.status.value,
                        database_webhook_url=form.webhook_url,
                        status_synchronized=False,
                        last_checked=datetime.now(),
                        issues=[f"Error during status check: {e}"],
                    )
                    status_results.append(error_status)
            return status_results

    async def track_webhook_operation(
        self,
        operation: str,
        onboarding_form_id: int,
        typeform_id: str,
        success: bool,
        webhook_url: str | None = None,
        error_message: str | None = None,
        webhook_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> WebhookOperationRecord:
        """Track webhook operation for auditing and monitoring.

        Args:
            operation: Type of operation performed.
            onboarding_form_id: Database onboarding form identifier.
            typeform_id: TypeForm form identifier.
            success: Whether the operation was successful.
            webhook_url: Webhook URL involved in the operation.
            error_message: Error message if operation failed.
            webhook_id: TypeForm webhook identifier.
            details: Additional operation details.

        Returns:
            WebhookOperationRecord for the tracked operation.
        """
        record = WebhookOperationRecord(
            operation=operation,
            onboarding_form_id=onboarding_form_id,
            typeform_id=typeform_id,
            webhook_url=webhook_url,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(),
            webhook_id=webhook_id,
        )
        if success:
            logger.info(
                "Webhook operation successful",
                operation=operation.upper(),
                onboarding_form_id=onboarding_form_id,
                webhook_id=webhook_id or 'N/A',
                action="webhook_operation_success"
            )
        else:
            logger.error(
                "Webhook operation failed",
                operation=operation.upper(),
                onboarding_form_id=onboarding_form_id,
                error_message=error_message,
                action="webhook_operation_failure"
            )
        return record

    async def synchronize_webhook_status(
        self, uow_factory: Callable[[],UnitOfWork], onboarding_form_id: int, force_update: bool = False
    ) -> bool:
        """Synchronize webhook status between database and TypeForm.

        Args:
            uow: Unit of work for database operations.
            onboarding_form_id: Database onboarding form identifier.
            force_update: Whether to force update even if already synchronized.

        Returns:
            True if synchronization was successful.

        Raises:
            WebhookConfigurationError: If form not found or synchronization fails.
        """
        logger.info("Synchronizing webhook status", onboarding_form_id=onboarding_form_id, action="webhook_sync_start")
        status_info = await self.get_comprehensive_webhook_status(
            uow_factory, onboarding_form_id
        )
        if status_info.status_synchronized and not force_update:
            logger.debug(
                "Webhook status already synchronized for form",
                onboarding_form_id=onboarding_form_id,
                action="webhook_sync_already_done"
            )
            return True
        async with uow_factory() as uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(
                    f"Onboarding form {onboarding_form_id} not found"
                )
            try:
                target_status = onboarding_form.status
                if status_info.webhook_exists and status_info.webhook_info:
                    if status_info.webhook_info.enabled:
                        target_status = OnboardingFormStatus.ACTIVE
                    else:
                        target_status = OnboardingFormStatus.PAUSED
                    if status_info.webhook_info.url != onboarding_form.webhook_url:
                        onboarding_form.webhook_url = status_info.webhook_info.url
                        logger.info(
                            "Updated webhook URL to match TypeForm",
                            new_url=status_info.webhook_info.url,
                            action="webhook_url_sync_update"
                        )
                elif onboarding_form.status == OnboardingFormStatus.ACTIVE:
                    target_status = OnboardingFormStatus.DRAFT
                    logger.warning(
                        "Webhook missing for active form, marking as draft",
                        onboarding_form_id=onboarding_form_id,
                        action="webhook_missing_mark_draft"
                    )
                if onboarding_form.status != target_status:
                    onboarding_form.status = target_status
                    onboarding_form.updated_at = datetime.now()
                    await uow.commit()
                    logger.info(
                        "Synchronized webhook status",
                        onboarding_form_id=onboarding_form_id,
                        target_status=target_status.value,
                        action="webhook_status_sync_success"
                    )
                    await self.track_webhook_operation(
                        operation="synchronize",
                        onboarding_form_id=onboarding_form_id,
                        typeform_id=onboarding_form.typeform_id,
                        success=True,
                        webhook_url=onboarding_form.webhook_url,
                    )
                else:
                    logger.debug(
                        "No status update needed for form",
                        onboarding_form_id=onboarding_form_id,
                        action="webhook_sync_no_update"
                    )
                return True
            except Exception as e:
                await uow.rollback()
                logger.error("Failed to synchronize webhook status", error=str(e), action="webhook_sync_failure")
                await self.track_webhook_operation(
                    operation="synchronize",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=False,
                    error_message=str(e),
                )
                raise

    async def _validate_form_ownership(self, typeform_id: str) -> FormInfo:
        try:
            form_info = await self.typeform_client.validate_form_access(typeform_id)
            return form_info
        except TypeFormFormNotFoundError:
            raise FormOwnershipError(
                typeform_id, message=f"Form {typeform_id} not found or access denied"
            ) from None
        except TypeFormAuthenticationError:
            raise FormOwnershipError(
                typeform_id,
                message=f"Invalid API key or insufficient permissions for form {typeform_id}",
            ) from None

    async def _create_onboarding_form_record(
        self, uow: UnitOfWork, user_id: str, typeform_id: str, webhook_url: str
    ) -> OnboardingForm:
        onboarding_form = OnboardingForm(
            user_id=user_id,
            typeform_id=typeform_id,
            webhook_url=webhook_url,
            status=OnboardingFormStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        async with uow:
            return await uow.onboarding_forms.add(onboarding_form)

    async def _setup_typeform_webhook(
        self, typeform_id: str, webhook_url: str
    ) -> WebhookInfo:
        try:
            existing_webhook = await self.typeform_client.get_webhook(
                typeform_id, self.webhook_tag
            )
            logger.info(
                "Found existing webhook, replacing with new webhook",
                existing_webhook_id=existing_webhook.id,
                action="webhook_replace_existing"
            )
            await self.typeform_client.delete_webhook(typeform_id, self.webhook_tag)
            logger.info("Deleted existing webhook", webhook_id=existing_webhook.id, action="webhook_delete_before_create")
            return await self.typeform_client.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url,
                tag=self.webhook_tag,
            )
        except (TypeFormWebhookNotFoundError, TypeFormFormNotFoundError):
            logger.info("Creating new webhook", typeform_id=typeform_id, action="webhook_create_new")
            return await self.typeform_client.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url,
                tag=self.webhook_tag,
            )

    def _check_status_synchronization(
        self,
        onboarding_form: OnboardingForm,
        webhook_info: WebhookInfo | None,
        webhook_exists: bool,
    ) -> bool:
        """Check if database status is synchronized with TypeForm webhook status.

        Args:
            onboarding_form: Database onboarding form record.
            webhook_info: TypeForm webhook information if exists.
            webhook_exists: Whether webhook exists in TypeForm.

        Returns:
            True if status is synchronized, False otherwise.
        """
        db_status = onboarding_form.status
        if not webhook_exists:
            return db_status in [
                OnboardingFormStatus.DRAFT,
                OnboardingFormStatus.DELETED,
            ]
        if webhook_info:
            if webhook_info.enabled:
                return db_status == OnboardingFormStatus.ACTIVE
            return db_status == OnboardingFormStatus.PAUSED
        return False


def create_webhook_manager(
    typeform_client: TypeFormClient | None = None,
) -> WebhookManager:
    return WebhookManager(typeform_client=typeform_client)
