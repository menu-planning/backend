from __future__ import annotations

# Re-export of the existing implementation to the new location.
# The content is moved verbatim from services/webhook_manager.py to maintain behavior.

import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingForm, OnboardingFormStatus
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.services.integrations.typeform.client import (
    TypeFormClient,
    WebhookInfo,
    FormInfo,
    create_typeform_client,
)
from src.contexts.client_onboarding.config import config
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookConfigurationError,
    FormOwnershipError,
    TypeFormFormNotFoundError,
    TypeFormAuthenticationError,
    TypeFormWebhookNotFoundError,
    TypeFormAPIError,
)


logger = logging.getLogger(__name__)


@dataclass
class WebhookStatusInfo:
    onboarding_form_id: int
    typeform_id: str
    webhook_exists: bool
    webhook_info: Optional[WebhookInfo]
    database_status: str
    database_webhook_url: Optional[str]
    status_synchronized: bool
    last_checked: datetime
    issues: List[str]


@dataclass
class WebhookOperationRecord:
    operation: str  # 'create', 'update', 'delete', 'enable', 'disable'
    onboarding_form_id: int
    typeform_id: str
    webhook_url: Optional[str]
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    webhook_id: Optional[str] = None


class WebhookManager:
    def __init__(self, typeform_client: Optional[TypeFormClient] = None):
        self.typeform_client = typeform_client or create_typeform_client()
        self.webhook_tag = "client_onboarding"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.typeform_client, 'close'):
            await self.typeform_client.close()

    async def setup_onboarding_form_webhook(
        self,
        uow: UnitOfWork,
        user_id: int,
        typeform_id: str,
        webhook_url: Optional[str] = None,
        validate_ownership: bool = True,
    ) -> Tuple[OnboardingForm, WebhookInfo]:
        logger.info(f"Setting up onboarding form webhook for user {user_id}, form {typeform_id}")
        if validate_ownership:
            try:
                form_info = await self.typeform_client.get_form(typeform_id)
                logger.info(f"Validated access to TypeForm: {form_info.title}")
            except TypeFormFormNotFoundError:
                # True 404 from Typeform
                logger.warning(
                    "TypeForm form not found or inaccessible",
                    extra={"typeform_id": typeform_id},
                )
                raise
            except TypeFormAuthenticationError as e:
                # Auth/permission problems – bubble up as-is
                logger.error(f"TypeForm authentication/authorization failed: {e}")
                raise
            except TypeFormAPIError as e:
                # API-level error surfaced from client – re-raise for accurate handling
                logger.error(f"TypeForm API error while validating form: {e}")
                raise
            except Exception as e:
                # Network/connectivity or unexpected error – don't mask as 404
                logger.error(
                    f"Network or unexpected error contacting TypeForm: {e}",
                )
                raise TypeFormAPIError(
                    message="Network error while contacting TypeForm",
                    status_code=503,
                    response_data={"detail": str(e)},
                )

        webhook_url = webhook_url or config.webhook_endpoint_url
        if not webhook_url:
            raise ValueError("Webhook URL must be provided or configured")

        try:
            async with uow:
                existing_form = await uow.onboarding_forms.get_by_typeform_id(typeform_id)
            if existing_form and existing_form.user_id != user_id:
                raise ValueError(f"TypeForm {typeform_id} is already associated with another user")

            if existing_form:
                logger.info(f"Form {typeform_id} already exists for user {user_id}")
                try:
                    webhook_info = await self.typeform_client.get_webhook(typeform_id, self.webhook_tag)
                    existing_form.webhook_url = webhook_url
                    await uow.commit()
                    return existing_form, webhook_info
                except (TypeFormWebhookNotFoundError, TypeFormFormNotFoundError):
                    logger.info(f"Webhook not found for existing form {typeform_id}, creating...")

            if not existing_form:
                onboarding_form = await self._create_onboarding_form_record(uow, user_id, typeform_id, webhook_url)
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
                details={"webhook_id": webhook_info.id, "webhook_tag": webhook_info.tag},
            )

            logger.info(f"Successfully set up onboarding form webhook: {onboarding_form.id}")
            return onboarding_form, webhook_info

        except Exception as e:
            logger.error(f"Failed to set up onboarding form webhook: {e}")
            await uow.rollback()
            onboarding_form_id = existing_form.id if 'existing_form' in locals() and existing_form else 0
            await self.track_webhook_operation(
                operation="setup_webhook",
                onboarding_form_id=onboarding_form_id,
                typeform_id=typeform_id,
                success=False,
                error_message=str(e),
                webhook_url=webhook_url,
            )
            raise

    async def update_webhook_url(self, uow: UnitOfWork, onboarding_form_id: int, new_webhook_url: str) -> WebhookInfo:
        logger.info(f"Updating webhook URL for onboarding form: {onboarding_form_id}")
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
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
                logger.info(f"Updated webhook URL for form {onboarding_form_id}: {new_webhook_url}")
                return webhook_info
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="update",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    webhook_url=new_webhook_url,
                    error_message=str(e),
                )
                logger.error(f"Failed to update webhook URL: {e}")
                raise

    async def disable_webhook(self, uow: UnitOfWork, onboarding_form_id: int) -> bool:
        logger.info(f"Disabling webhook for onboarding form: {onboarding_form_id}")
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
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
                logger.info(f"Disabled webhook for onboarding form: {onboarding_form_id}")
                return True
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="disable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    error_message=str(e),
                )
                logger.error(f"Failed to disable webhook: {e}")
                raise

    async def enable_webhook(self, uow: UnitOfWork, onboarding_form_id: int) -> bool:
        logger.info(f"Enabling webhook for onboarding form: {onboarding_form_id}")
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
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
                logger.info(f"Enabled webhook for onboarding form: {onboarding_form_id}")
                return True
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="enable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    error_message=str(e),
                )
                logger.error(f"Failed to enable webhook: {e}")
                raise

    async def delete_webhook_configuration(self, uow: UnitOfWork, onboarding_form_id: int) -> bool:
        logger.info(f"Deleting webhook configuration for onboarding form: {onboarding_form_id}")
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
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
                logger.info(f"Deleted webhook configuration for onboarding form: {onboarding_form_id}")
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
                logger.info(f"Webhook already deleted, updated database status: {onboarding_form_id}")
                return True
            except Exception as e:
                await uow.rollback()
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    error_message=str(e),
                )
                logger.error(f"Failed to delete webhook configuration: {e}")
                raise

    async def get_webhook_status(self, uow: UnitOfWork, onboarding_form_id: int) -> Optional[WebhookInfo]:
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            try:
                webhook_info = await self.typeform_client.get_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                )
                return webhook_info
            except TypeFormFormNotFoundError:
                logger.warning(f"Webhook not found for onboarding form: {onboarding_form_id}")
                return None

    async def list_user_onboarding_forms(self, uow: UnitOfWork, user_id: int) -> List[OnboardingForm]:
        async with uow:
            return await uow.onboarding_forms.get_by_user_id(user_id)

    async def get_comprehensive_webhook_status(self, uow: UnitOfWork, onboarding_form_id: int) -> WebhookStatusInfo:
        logger.info(f"Getting comprehensive webhook status for form: {onboarding_form_id}")
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            issues: List[str] = []
            webhook_info: Optional[WebhookInfo] = None
            webhook_exists = False
            try:
                webhook_info = await self.typeform_client.get_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                )
                webhook_exists = True
                logger.debug(f"Webhook found: {webhook_info.id}")
            except TypeFormFormNotFoundError:
                logger.debug(f"No webhook found for form: {onboarding_form.typeform_id}")
                webhook_exists = False
            except Exception as e:
                issues.append(f"Error checking webhook status: {e}")
                logger.warning(f"Error checking webhook status: {e}")

            status_synchronized = self._check_status_synchronization(onboarding_form, webhook_info, webhook_exists)
            if not status_synchronized:
                issues.append("Database and TypeForm webhook status not synchronized")

            if webhook_exists and webhook_info and onboarding_form.webhook_url:
                if webhook_info.url != onboarding_form.webhook_url:
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

    async def bulk_webhook_status_check(self, uow: UnitOfWork, user_id: int, include_deleted: bool = False) -> List[WebhookStatusInfo]:
        logger.info(f"Performing bulk webhook status check - User: {user_id}, Include deleted: {include_deleted}")
        async with uow:
            forms = await uow.onboarding_forms.get_by_user_id(user_id)
            if not include_deleted:
                forms = [f for f in forms if f.status != OnboardingFormStatus.DELETED]
            logger.info(f"Checking {len(forms)} onboarding forms for user {user_id}")
            status_results: List[WebhookStatusInfo] = []
            for form in forms:
                try:
                    status_info = await self.get_comprehensive_webhook_status(uow, form.id)
                    status_results.append(status_info)
                except Exception as e:
                    logger.error(f"Error checking status for form {form.id}: {e}")
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
        webhook_url: Optional[str] = None,
        error_message: Optional[str] = None,
        webhook_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> WebhookOperationRecord:
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
                f"Webhook operation successful - {operation.upper()}: "
                f"Form {onboarding_form_id}, Webhook {webhook_id or 'N/A'}"
            )
        else:
            logger.error(
                f"Webhook operation failed - {operation.upper()}: "
                f"Form {onboarding_form_id}, Error: {error_message}"
            )
        return record

    async def synchronize_webhook_status(self, uow: UnitOfWork, onboarding_form_id: int, force_update: bool = False) -> bool:
        logger.info(f"Synchronizing webhook status for form: {onboarding_form_id}")
        status_info = await self.get_comprehensive_webhook_status(uow, onboarding_form_id)
        if status_info.status_synchronized and not force_update:
            logger.debug(f"Webhook status already synchronized for form: {onboarding_form_id}")
            return True
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            try:
                target_status = onboarding_form.status
                if status_info.webhook_exists and status_info.webhook_info:
                    if status_info.webhook_info.enabled:
                        target_status = OnboardingFormStatus.ACTIVE
                    else:
                        target_status = OnboardingFormStatus.PAUSED
                    if status_info.webhook_info.url != onboarding_form.webhook_url:
                        onboarding_form.webhook_url = status_info.webhook_info.url
                        logger.info(f"Updated webhook URL to match TypeForm: {status_info.webhook_info.url}")
                else:
                    if onboarding_form.status == OnboardingFormStatus.ACTIVE:
                        target_status = OnboardingFormStatus.DRAFT
                        logger.warning(
                            f"Webhook missing for active form, marking as draft: {onboarding_form_id}"
                        )
                if onboarding_form.status != target_status:
                    onboarding_form.status = target_status
                    onboarding_form.updated_at = datetime.now()
                    await uow.commit()
                    logger.info(
                        f"Synchronized webhook status: {onboarding_form_id} -> {target_status.value}"
                    )
                    await self.track_webhook_operation(
                        operation="synchronize",
                        onboarding_form_id=onboarding_form_id,
                        typeform_id=onboarding_form.typeform_id,
                        success=True,
                        webhook_url=onboarding_form.webhook_url,
                    )
                else:
                    logger.debug(f"No status update needed for form: {onboarding_form_id}")
                return True
            except Exception as e:
                await uow.rollback()
                logger.error(f"Failed to synchronize webhook status: {e}")
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
            raise FormOwnershipError(typeform_id, message=f"Form {typeform_id} not found or access denied")
        except TypeFormAuthenticationError:
            raise FormOwnershipError(
                typeform_id, message=f"Invalid API key or insufficient permissions for form {typeform_id}"
            )

    async def _create_onboarding_form_record(self, uow: UnitOfWork, user_id: int, typeform_id: str, webhook_url: str) -> OnboardingForm:
        onboarding_form = OnboardingForm(
            user_id=user_id,
            typeform_id=typeform_id,
            webhook_url=webhook_url,
            status=OnboardingFormStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return await uow.onboarding_forms.add(onboarding_form)

    async def _setup_typeform_webhook(self, typeform_id: str, webhook_url: str) -> WebhookInfo:
        try:
            existing_webhook = await self.typeform_client.get_webhook(typeform_id, self.webhook_tag)
            logger.info(f"Found existing webhook {existing_webhook.id}, replacing with new webhook")
            await self.typeform_client.delete_webhook(typeform_id, self.webhook_tag)
            logger.info(f"Deleted existing webhook {existing_webhook.id}")
            return await self.typeform_client.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url,
                tag=self.webhook_tag,
            )
        except (TypeFormWebhookNotFoundError, TypeFormFormNotFoundError):
            logger.info(f"Creating new webhook for form {typeform_id}")
            return await self.typeform_client.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url,
                tag=self.webhook_tag,
            )

    def _check_status_synchronization(
        self,
        onboarding_form: OnboardingForm,
        webhook_info: Optional[WebhookInfo],
        webhook_exists: bool,
    ) -> bool:
        """Check if DB status is synchronized with TypeForm webhook status."""
        db_status = onboarding_form.status
        if not webhook_exists:
            return db_status in [OnboardingFormStatus.DRAFT, OnboardingFormStatus.DELETED]
        if webhook_info:
            if webhook_info.enabled:
                return db_status == OnboardingFormStatus.ACTIVE
            else:
                return db_status == OnboardingFormStatus.PAUSED
        return False


def create_webhook_manager(typeform_client: Optional[TypeFormClient] = None) -> WebhookManager:
    return WebhookManager(typeform_client=typeform_client)


