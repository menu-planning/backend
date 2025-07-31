"""
Webhook Configuration Service

High-level service for managing TypeForm webhooks for client onboarding forms.
Handles webhook lifecycle, form ownership validation, and database integration.
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from ..models.onboarding_form import OnboardingForm, OnboardingFormStatus
from ..core.services.uow import UnitOfWork
from .typeform_client import (
    TypeFormClient, 
    WebhookInfo, 
    FormInfo,
    TypeFormAPIError,
    TypeFormNotFoundError,
    TypeFormAuthenticationError,
    create_typeform_client,
    TypeFormValidationError,
    TypeFormWebhookNotFoundError
)
from ..config import config
from .exceptions import (
    WebhookConfigurationError,
    FormOwnershipError,
    WebhookAlreadyExistsError,
    WebhookOperationError,
    WebhookSynchronizationError,
    WebhookStatusError,
    WebhookLifecycleError,
    BulkWebhookOperationError,
    TypeFormWebhookNotFoundError
)


logger = logging.getLogger(__name__)


@dataclass
class WebhookStatusInfo:
    """Comprehensive webhook status information."""
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
    """Record of webhook operation for tracking."""
    operation: str  # 'create', 'update', 'delete', 'enable', 'disable'
    onboarding_form_id: int
    typeform_id: str
    webhook_url: Optional[str]
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    webhook_id: Optional[str] = None


class WebhookManager:
    """
    Service for managing TypeForm webhooks for onboarding forms.
    
    Provides high-level operations for:
    - Setting up webhooks for new onboarding forms
    - Validating form ownership before webhook configuration
    - Managing webhook lifecycle (create, update, disable, delete)
    - Synchronizing webhook state with database records
    """
    
    def __init__(self, typeform_client: Optional[TypeFormClient] = None):
        """
        Initialize webhook manager.
        
        Args:
            typeform_client: Optional TypeForm client (creates default if None)
        """
        self.typeform_client = typeform_client or create_typeform_client()
        self.webhook_tag = "client_onboarding"
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.typeform_client, 'close'):
            await self.typeform_client.close()
    
    async def setup_onboarding_form_webhook(
        self,
        uow: UnitOfWork,
        user_id: int,
        typeform_id: str,
        webhook_url: Optional[str] = None,
        validate_ownership: bool = True
    ) -> Tuple[OnboardingForm, WebhookInfo]:
        """
        Set up a complete onboarding form with TypeForm webhook integration.
        
        Args:
            uow: Unit of work for database operations
            user_id: User ID who owns this onboarding form
            typeform_id: TypeForm form ID
            webhook_url: Custom webhook URL (uses config default if None)
            validate_ownership: Whether to validate API key access to form
            
        Returns:
            Tuple of (OnboardingForm record, WebhookInfo from TypeForm)
            
        Raises:
            TypeFormValidationError: If form is not accessible or invalid
            TypeFormWebhookCreationError: If webhook creation fails
            DatabaseOperationError: If database operations fail
            ValueError: If parameters are invalid
        """
        logger.info(f"Setting up onboarding form webhook for user {user_id}, form {typeform_id}")
        
        # Validate form access with TypeForm if requested
        if validate_ownership:
            try:
                form_info = await self.typeform_client.get_form(typeform_id)
                logger.info(f"Validated access to TypeForm: {form_info.title}")
            except Exception as e:
                logger.error(f"Failed to validate TypeForm access: {e}")
                raise TypeFormValidationError(f"Cannot access TypeForm {typeform_id}: {e}")
        
        # Use configured webhook URL if none provided
        webhook_url = webhook_url or config.webhook_endpoint_url
        if not webhook_url:
            raise ValueError("Webhook URL must be provided or configured")
        
        # Check if form already exists for this user
        try:
            existing_form = await uow.onboarding_forms.get_by_typeform_id(typeform_id)
            if existing_form and existing_form.user_id != user_id:
                raise ValueError(f"TypeForm {typeform_id} is already associated with another user")
            
            if existing_form:
                logger.info(f"Form {typeform_id} already exists for user {user_id}")
                
                # Get current webhook information from TypeForm
                try:
                    webhook_info = await self.typeform_client.get_webhook(typeform_id, self.webhook_tag)
                    return existing_form, webhook_info
                except TypeFormWebhookNotFoundError:
                    # Webhook doesn't exist, create it
                    logger.info(f"Webhook not found for existing form {typeform_id}, creating...")
        
            # Create onboarding form record if it doesn't exist
            if not existing_form:
                onboarding_form = await self._create_onboarding_form_record(uow, user_id, typeform_id, webhook_url)
            else:
                onboarding_form = existing_form
            
            # Create or update webhook in TypeForm
            webhook_info = await self._setup_typeform_webhook(typeform_id, webhook_url)
            
            # Save changes to database
            await uow.commit()
            
            # Track successful operation
            await self.track_webhook_operation(
                operation="setup_webhook",
                onboarding_form_id=onboarding_form.id,
                typeform_id=typeform_id,
                success=True,
                webhook_url=webhook_url,
                details={"webhook_id": webhook_info.id, "webhook_tag": webhook_info.tag}
            )
            
            logger.info(f"Successfully set up onboarding form webhook: {onboarding_form.id}")
            return onboarding_form, webhook_info
            
        except Exception as e:
            logger.error(f"Failed to set up onboarding form webhook: {e}")
            await uow.rollback()
            
            # Track failed operation - handle case where onboarding_form might not exist
            onboarding_form_id = existing_form.id if 'existing_form' in locals() and existing_form else 0
            await self.track_webhook_operation(
                operation="setup_webhook",
                onboarding_form_id=onboarding_form_id,
                typeform_id=typeform_id,
                success=False,
                error_message=str(e),
                webhook_url=webhook_url
            )
            
            raise
    
    async def update_webhook_url(self, uow: UnitOfWork, onboarding_form_id: int, new_webhook_url: str) -> WebhookInfo:
        """
        Update webhook URL for an existing onboarding form.
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            new_webhook_url: New webhook URL to configure
            
        Returns:
            Updated webhook information
            
        Raises:
            WebhookConfigurationError: If form not found or update fails
        """
        logger.info(f"Updating webhook URL for onboarding form: {onboarding_form_id}")
        
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            
            try:
                # Update TypeForm webhook
                webhook_info = await self.typeform_client.update_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                    webhook_url=new_webhook_url
                )
                
                # Update database record
                onboarding_form.webhook_url = new_webhook_url
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                
                # Track the successful update operation
                await self.track_webhook_operation(
                    operation="update",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=new_webhook_url,
                    webhook_id=webhook_info.id
                )
                
                logger.info(f"Updated webhook URL for form {onboarding_form_id}: {new_webhook_url}")
                return webhook_info
                
            except Exception as e:
                await uow.rollback()
                
                # Track the failed update operation
                await self.track_webhook_operation(
                    operation="update",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    webhook_url=new_webhook_url,
                    error_message=str(e)
                )
                
                logger.error(f"Failed to update webhook URL: {e}")
                raise
    
    async def disable_webhook(self, uow: UnitOfWork, onboarding_form_id: int) -> bool:
        """
        Disable webhook for an onboarding form (pauses the form).
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            
        Returns:
            True if successfully disabled
        """
        logger.info(f"Disabling webhook for onboarding form: {onboarding_form_id}")
        
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            
            try:
                # Disable TypeForm webhook
                webhook_info = await self.typeform_client.update_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                    enabled=False
                )
                
                # Update form status
                onboarding_form.status = OnboardingFormStatus.PAUSED
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                
                # Track the successful disable operation
                await self.track_webhook_operation(
                    operation="disable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url
                )
                
                logger.info(f"Disabled webhook for onboarding form: {onboarding_form_id}")
                return True
                
            except Exception as e:
                await uow.rollback()
                
                # Track the failed disable operation
                await self.track_webhook_operation(
                    operation="disable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    error_message=str(e)
                )
                
                logger.error(f"Failed to disable webhook: {e}")
                raise
    
    async def enable_webhook(self, uow: UnitOfWork, onboarding_form_id: int) -> bool:
        """
        Enable webhook for a paused onboarding form.
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            
        Returns:
            True if successfully enabled
        """
        logger.info(f"Enabling webhook for onboarding form: {onboarding_form_id}")
        
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            
            try:
                # Enable TypeForm webhook
                webhook_info = await self.typeform_client.update_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag,
                    enabled=True
                )
                
                # Update form status
                onboarding_form.status = OnboardingFormStatus.ACTIVE
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                
                # Track the successful enable operation
                await self.track_webhook_operation(
                    operation="enable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url
                )
                
                logger.info(f"Enabled webhook for onboarding form: {onboarding_form_id}")
                return True
                
            except Exception as e:
                await uow.rollback()
                
                # Track the failed enable operation
                await self.track_webhook_operation(
                    operation="enable",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    error_message=str(e)
                )
                
                logger.error(f"Failed to enable webhook: {e}")
                raise
    
    async def delete_webhook_configuration(self, uow: UnitOfWork, onboarding_form_id: int) -> bool:
        """
        Delete webhook configuration and mark onboarding form as deleted.
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            
        Returns:
            True if successfully deleted
        """
        logger.info(f"Deleting webhook configuration for onboarding form: {onboarding_form_id}")
        
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            
            try:
                # Delete TypeForm webhook
                await self.typeform_client.delete_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag
                )
                
                # Mark form as deleted (soft delete)
                onboarding_form.status = OnboardingFormStatus.DELETED
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                
                # Track the successful delete operation
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url
                )
                
                logger.info(f"Deleted webhook configuration for onboarding form: {onboarding_form_id}")
                return True
                
            except TypeFormNotFoundError:
                # Webhook already doesn't exist, just update database
                onboarding_form.status = OnboardingFormStatus.DELETED
                onboarding_form.updated_at = datetime.now()
                await uow.commit()
                
                # Track the delete operation (webhook already missing)
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=True,
                    webhook_url=onboarding_form.webhook_url,
                    error_message="Webhook already deleted in TypeForm"
                )
                
                logger.info(f"Webhook already deleted, updated database status: {onboarding_form_id}")
                return True
            except Exception as e:
                await uow.rollback()
                
                # Track the failed delete operation
                await self.track_webhook_operation(
                    operation="delete",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id if 'onboarding_form' in locals() else "unknown",
                    success=False,
                    error_message=str(e)
                )
                
                logger.error(f"Failed to delete webhook configuration: {e}")
                raise
    
    async def get_webhook_status(self, uow: UnitOfWork, onboarding_form_id: int) -> Optional[WebhookInfo]:
        """
        Get current webhook status from TypeForm for an onboarding form.
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            
        Returns:
            Current webhook information or None if not found
        """
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            
            try:
                webhook_info = await self.typeform_client.get_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag
                )
                return webhook_info
            except TypeFormNotFoundError:
                logger.warning(f"Webhook not found for onboarding form: {onboarding_form_id}")
                return None
    
    async def list_user_onboarding_forms(self, uow: UnitOfWork, user_id: int) -> List[OnboardingForm]:
        """
        List all onboarding forms for a specific user.
        
        Args:
            uow: Unit of work for database operations
            user_id: User ID
            
        Returns:
            List of onboarding forms
        """
        async with uow:
            return await uow.onboarding_forms.get_by_user_id(user_id)
    
    async def get_comprehensive_webhook_status(
        self, 
        uow: UnitOfWork, 
        onboarding_form_id: int
    ) -> WebhookStatusInfo:
        """
        Get comprehensive webhook status with synchronization checking.
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            
        Returns:
            Comprehensive webhook status information
        """
        logger.info(f"Getting comprehensive webhook status for form: {onboarding_form_id}")
        
        async with uow:
            onboarding_form = await uow.onboarding_forms.get_by_id(onboarding_form_id)
            if not onboarding_form:
                raise WebhookConfigurationError(f"Onboarding form {onboarding_form_id} not found")
            
            issues = []
            webhook_info = None
            webhook_exists = False
            
            # Check TypeForm webhook status
            try:
                webhook_info = await self.typeform_client.get_webhook(
                    form_id=onboarding_form.typeform_id,
                    tag=self.webhook_tag
                )
                webhook_exists = True
                logger.debug(f"Webhook found: {webhook_info.id}")
            except TypeFormNotFoundError:
                logger.debug(f"No webhook found for form: {onboarding_form.typeform_id}")
                webhook_exists = False
            except Exception as e:
                issues.append(f"Error checking webhook status: {e}")
                logger.warning(f"Error checking webhook status: {e}")
            
            # Check synchronization between database and TypeForm
            status_synchronized = self._check_status_synchronization(
                onboarding_form, webhook_info, webhook_exists
            )
            if not status_synchronized:
                issues.append("Database and TypeForm webhook status not synchronized")
            
            # Check URL synchronization
            if webhook_exists and webhook_info and onboarding_form.webhook_url:
                if webhook_info.url != onboarding_form.webhook_url:
                    issues.append(f"Webhook URL mismatch: DB={onboarding_form.webhook_url}, TypeForm={webhook_info.url}")
            
            return WebhookStatusInfo(
                onboarding_form_id=onboarding_form_id,
                typeform_id=onboarding_form.typeform_id,
                webhook_exists=webhook_exists,
                webhook_info=webhook_info,
                database_status=onboarding_form.status.value,
                database_webhook_url=onboarding_form.webhook_url,
                status_synchronized=status_synchronized,
                last_checked=datetime.now(),
                issues=issues
            )
    
    async def bulk_webhook_status_check(
        self, 
        uow: UnitOfWork, 
        user_id: int,
        include_deleted: bool = False
    ) -> List[WebhookStatusInfo]:
        """
        Perform bulk webhook status check for multiple forms.
        
        Args:
            uow: Unit of work for database operations
            user_id: User ID to filter forms (required for security)
            include_deleted: Whether to include deleted forms in check
            
        Returns:
            List of webhook status information for all checked forms
        """
        logger.info(f"Performing bulk webhook status check - User: {user_id}, Include deleted: {include_deleted}")
        
        async with uow:
            # Get forms to check for the specific user
            forms = await uow.onboarding_forms.get_by_user_id(user_id)
            
            if not include_deleted:
                forms = [f for f in forms if f.status != OnboardingFormStatus.DELETED]
            
            logger.info(f"Checking {len(forms)} onboarding forms for user {user_id}")
            
            status_results = []
            for form in forms:
                try:
                    status_info = await self.get_comprehensive_webhook_status(uow, form.id)
                    status_results.append(status_info)
                except Exception as e:
                    logger.error(f"Error checking status for form {form.id}: {e}")
                    # Create error status info
                    error_status = WebhookStatusInfo(
                        onboarding_form_id=form.id,
                        typeform_id=form.typeform_id,
                        webhook_exists=False,
                        webhook_info=None,
                        database_status=form.status.value,
                        database_webhook_url=form.webhook_url,
                        status_synchronized=False,
                        last_checked=datetime.now(),
                        issues=[f"Error during status check: {e}"]
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
        details: Optional[Dict[str, Any]] = None
    ) -> WebhookOperationRecord:
        """
        Track webhook operation for monitoring and debugging.
        
        Args:
            operation: Operation type ('create', 'update', 'delete', 'enable', 'disable')
            onboarding_form_id: OnboardingForm record ID
            typeform_id: TypeForm form ID
            success: Whether operation was successful
            webhook_url: Webhook URL (for applicable operations)
            error_message: Error message if operation failed
            webhook_id: TypeForm webhook ID (if available)
            details: Additional details to log
            
        Returns:
            Operation record for logging/storage
        """
        record = WebhookOperationRecord(
            operation=operation,
            onboarding_form_id=onboarding_form_id,
            typeform_id=typeform_id,
            webhook_url=webhook_url,
            success=success,
            error_message=error_message,
            timestamp=datetime.now(),
            webhook_id=webhook_id
        )
        
        # Log the operation
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
        
        # In a production system, you might want to store these records
        # For now, we'll just return the record for potential logging/storage
        return record
    
    async def synchronize_webhook_status(
        self, 
        uow: UnitOfWork, 
        onboarding_form_id: int,
        force_update: bool = False
    ) -> bool:
        """
        Synchronize database status with actual TypeForm webhook status.
        
        Args:
            uow: Unit of work for database operations
            onboarding_form_id: OnboardingForm record ID
            force_update: Whether to force update even if status appears synchronized
            
        Returns:
            True if synchronization was performed or status was already synchronized
        """
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
                # Determine correct status based on TypeForm state
                if status_info.webhook_exists and status_info.webhook_info:
                    if status_info.webhook_info.enabled:
                        target_status = OnboardingFormStatus.ACTIVE
                    else:
                        target_status = OnboardingFormStatus.PAUSED
                    
                    # Update URL if different
                    if status_info.webhook_info.url != onboarding_form.webhook_url:
                        onboarding_form.webhook_url = status_info.webhook_info.url
                        logger.info(f"Updated webhook URL to match TypeForm: {status_info.webhook_info.url}")
                        
                else:
                    # No webhook exists, form should be marked appropriately
                    if onboarding_form.status == OnboardingFormStatus.ACTIVE:
                        target_status = OnboardingFormStatus.DRAFT  # Reset to draft if webhook missing
                        logger.warning(f"Webhook missing for active form, marking as draft: {onboarding_form_id}")
                
                # Update status if needed
                if onboarding_form.status != target_status:
                    onboarding_form.status = target_status
                    onboarding_form.updated_at = datetime.now()
                    await uow.commit()
                    
                    logger.info(f"Synchronized webhook status: {onboarding_form_id} -> {target_status.value}")
                    
                    # Track the synchronization operation
                    await self.track_webhook_operation(
                        operation="synchronize",
                        onboarding_form_id=onboarding_form_id,
                        typeform_id=onboarding_form.typeform_id,
                        success=True,
                        webhook_url=onboarding_form.webhook_url
                    )
                else:
                    logger.debug(f"No status update needed for form: {onboarding_form_id}")
                
                return True
                
            except Exception as e:
                await uow.rollback()
                logger.error(f"Failed to synchronize webhook status: {e}")
                
                # Track the failed synchronization
                await self.track_webhook_operation(
                    operation="synchronize",
                    onboarding_form_id=onboarding_form_id,
                    typeform_id=onboarding_form.typeform_id,
                    success=False,
                    error_message=str(e)
                )
                raise

    # Private helper methods
    
    async def _validate_form_ownership(self, typeform_id: str) -> FormInfo:
        """Validate that current API key has access to the form."""
        try:
            form_info = await self.typeform_client.validate_form_access(typeform_id)
            return form_info
        except TypeFormNotFoundError:
            raise FormOwnershipError(typeform_id, message=f"Form {typeform_id} not found or access denied")
        except TypeFormAuthenticationError:
            raise FormOwnershipError(typeform_id, message=f"Invalid API key or insufficient permissions for form {typeform_id}")
    
    async def _create_onboarding_form_record(self, uow: UnitOfWork, user_id: int, typeform_id: str, webhook_url: str) -> OnboardingForm:
        """Create a new OnboardingForm record."""
        onboarding_form = OnboardingForm(
            user_id=user_id,
            typeform_id=typeform_id,
            title=f"Onboarding Form {typeform_id}",
            description="Auto-generated onboarding form",
            webhook_url=webhook_url,
            status=OnboardingFormStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        return await uow.onboarding_forms.add(onboarding_form)
    
    async def _setup_typeform_webhook(self, typeform_id: str, webhook_url: str) -> WebhookInfo:
        """Configure TypeForm webhook for the form."""
        try:
            # Check if webhook already exists
            existing_webhook = await self.typeform_client.get_webhook(typeform_id, self.webhook_tag)
            logger.info(f"Found existing webhook {existing_webhook.id}, updating URL")
            
            # Update existing webhook
            return await self.typeform_client.update_webhook(
                form_id=typeform_id,
                tag=self.webhook_tag,
                webhook_url=webhook_url
            )
        except TypeFormWebhookNotFoundError:
            # Create new webhook
            logger.info(f"Creating new webhook for form {typeform_id}")
            return await self.typeform_client.create_webhook(
                form_id=typeform_id,
                webhook_url=webhook_url,
                tag=self.webhook_tag
            )

    def _check_status_synchronization(
        self, 
        onboarding_form: OnboardingForm, 
        webhook_info: Optional[WebhookInfo], 
        webhook_exists: bool
    ) -> bool:
        """
        Check if database status is synchronized with TypeForm webhook status.
        
        Args:
            onboarding_form: Database onboarding form record
            webhook_info: TypeForm webhook information (if exists)
            webhook_exists: Whether webhook exists in TypeForm
            
        Returns:
            True if status is synchronized
        """
        db_status = onboarding_form.status
        
        if not webhook_exists:
            # No webhook exists - form should be DRAFT or DELETED
            return db_status in [OnboardingFormStatus.DRAFT, OnboardingFormStatus.DELETED]
        
        if webhook_info:
            if webhook_info.enabled:
                # Webhook is enabled - form should be ACTIVE
                return db_status == OnboardingFormStatus.ACTIVE
            else:
                # Webhook is disabled - form should be PAUSED
                return db_status == OnboardingFormStatus.PAUSED
        
        # Default to not synchronized if we can't determine
        return False


# Convenience function for creating webhook manager instances
def create_webhook_manager(typeform_client: Optional[TypeFormClient] = None) -> WebhookManager:
    """
    Create a webhook manager instance.
    
    Args:
        typeform_client: Optional TypeForm client (uses default if not provided)
        
    Returns:
        Configured webhook manager
    """
    return WebhookManager(typeform_client=typeform_client) 