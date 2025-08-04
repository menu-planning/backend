"""
Custom exceptions for TypeForm API integration and client onboarding validation.

This module defines the exception hierarchy for handling TypeForm API failures,
validation errors, and webhook processing issues in the client onboarding context.
"""

from typing import Optional, Dict, Any


class ClientOnboardingError(Exception):
    """Base exception for all client onboarding related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class TypeFormAPIError(ClientOnboardingError):
    """Base exception for TypeForm API related errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, details)
        self.status_code = status_code
        self.response_data = response_data or {}
        self.retry_after = retry_after


class TypeFormAuthenticationError(TypeFormAPIError):
    """Raised when TypeForm API authentication fails."""
    
    def __init__(self, message: str = "TypeForm API authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class TypeFormFormNotFoundError(TypeFormAPIError):
    """Raised when a TypeForm form cannot be found or accessed."""
    
    def __init__(self, form_id: str, **kwargs):
        message = f"TypeForm form not found or inaccessible: {form_id}"
        super().__init__(message, **kwargs)
        self.form_id = form_id


class TypeFormWebhookError(TypeFormAPIError):
    """Base exception for TypeForm webhook operations."""
    pass


class TypeFormWebhookCreationError(TypeFormWebhookError):
    """Raised when webhook creation fails."""
    
    def __init__(self, webhook_url: str, reason: str, **kwargs):
        message = f"Failed to create TypeForm webhook for URL {webhook_url}: {reason}"
        super().__init__(message, **kwargs)
        self.webhook_url = webhook_url
        self.reason = reason


class TypeFormWebhookNotFoundError(TypeFormWebhookError):
    """Raised when a webhook cannot be found for deletion/update."""
    
    def __init__(self, webhook_id: str, **kwargs):
        message = f"TypeForm webhook not found: {webhook_id}"
        super().__init__(message, **kwargs)
        self.webhook_id = webhook_id


# Webhook Management Exceptions
class WebhookConfigurationError(TypeFormWebhookError):
    """Base exception for webhook configuration and management errors."""
    
    def __init__(self, message: str, form_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.form_id = form_id


class FormOwnershipError(WebhookConfigurationError):
    """Raised when form ownership validation fails during webhook management."""
    
    def __init__(self, form_id: str, user_id: Optional[int] = None, **kwargs):
        if user_id:
            message = f"User {user_id} does not own TypeForm form {form_id}"
        else:
            message = f"Form ownership validation failed for TypeForm form {form_id}"
        super().__init__(message, form_id=form_id, **kwargs)
        self.user_id = user_id


class WebhookAlreadyExistsError(WebhookConfigurationError):
    """Raised when attempting to create a webhook that already exists."""
    
    def __init__(self, form_id: str, webhook_tag: str, **kwargs):
        message = f"Webhook with tag '{webhook_tag}' already exists for form {form_id}"
        super().__init__(message, form_id=form_id, **kwargs)
        self.webhook_tag = webhook_tag


class WebhookOperationError(WebhookConfigurationError):
    """Raised when webhook lifecycle operations fail."""
    
    def __init__(self, operation: str, form_id: str, reason: str, **kwargs):
        message = f"Webhook {operation} operation failed for form {form_id}: {reason}"
        super().__init__(message, form_id=form_id, **kwargs)
        self.operation = operation
        self.reason = reason


class WebhookSynchronizationError(WebhookConfigurationError):
    """Raised when webhook status synchronization between database and TypeForm fails."""
    
    def __init__(self, form_id: str, sync_issue: str, **kwargs):
        message = f"Webhook synchronization failed for form {form_id}: {sync_issue}"
        super().__init__(message, form_id=form_id, **kwargs)
        self.sync_issue = sync_issue


class WebhookStatusError(WebhookConfigurationError):
    """Raised when webhook status checking or validation fails."""
    
    def __init__(self, form_id: str, status_issue: str, **kwargs):
        message = f"Webhook status error for form {form_id}: {status_issue}"
        super().__init__(message, form_id=form_id, **kwargs)
        self.status_issue = status_issue


class WebhookLifecycleError(WebhookConfigurationError):
    """Raised when webhook lifecycle management encounters errors."""
    
    def __init__(self, lifecycle_stage: str, form_id: str, details: str, **kwargs):
        message = f"Webhook lifecycle error during {lifecycle_stage} for form {form_id}: {details}"
        super().__init__(message, form_id=form_id, **kwargs)
        self.lifecycle_stage = lifecycle_stage
        self.details = details


class BulkWebhookOperationError(WebhookConfigurationError):
    """Raised when bulk webhook operations encounter failures."""
    
    def __init__(self, total_operations: int, failed_operations: int, error_details: Dict[str, str], **kwargs):
        message = f"Bulk webhook operation failed: {failed_operations}/{total_operations} operations failed"
        super().__init__(message, **kwargs)
        self.total_operations = total_operations
        self.failed_operations = failed_operations
        self.error_details = error_details
        self.success_rate = (total_operations - failed_operations) / total_operations * 100


class TypeFormRateLimitError(Exception):
    """Raised when TypeForm API rate limit is exceeded."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None, retry_after: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        self.retry_after = retry_after
        super().__init__(self.message)


class FormValidationError(ClientOnboardingError):
    """Raised when form configuration validation fails."""
    
    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        message = f"Form validation failed for field '{field}' with value '{value}': {reason}"
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        self.reason = reason


class WebhookSecurityError(ClientOnboardingError):
    """Raised when webhook security validation fails."""
    
    def __init__(self, reason: str, **kwargs):
        message = f"Webhook security validation failed: {reason}"
        super().__init__(message, **kwargs)
        self.reason = reason


class WebhookSignatureError(WebhookSecurityError):
    """Raised when webhook signature verification fails."""
    
    def __init__(self, 
                 reason: str,
                 expected_signature: Optional[str] = None, 
                 received_signature: Optional[str] = None,
                 source_ip: Optional[str] = None,
                 payload_hash: Optional[str] = None,
                 **kwargs):
        message = f"Webhook signature verification failed: {reason}"
        super().__init__(message, **kwargs)
        self.reason = reason
        self.expected_signature = expected_signature
        self.received_signature = received_signature
        self.source_ip = source_ip
        self.payload_hash = payload_hash
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception details to dictionary for logging."""
        return {
            "error_type": "WebhookSignatureError",
            "reason": self.reason,
            "source_ip": self.source_ip,
            "payload_hash": self.payload_hash,
            "has_expected_signature": self.expected_signature is not None,
            "has_received_signature": self.received_signature is not None
        }


class WebhookPayloadError(ClientOnboardingError):
    """Raised when webhook payload processing fails."""
    
    def __init__(self, payload_issue: str, payload_data: Optional[Dict[str, Any]] = None, **kwargs):
        message = f"Webhook payload processing failed: {payload_issue}"
        super().__init__(message, **kwargs)
        self.payload_issue = payload_issue
        self.payload_data = payload_data or {}


class OnboardingFormNotFoundError(ClientOnboardingError):
    """Raised when an onboarding form cannot be found in the database."""
    
    def __init__(self, identifier: str, identifier_type: str = "id", **kwargs):
        message = f"Onboarding form not found by {identifier_type}: {identifier}"
        super().__init__(message, **kwargs)
        self.identifier = identifier
        self.identifier_type = identifier_type


class OnboardingFormAccessError(ClientOnboardingError):
    """Raised when user lacks access to an onboarding form."""
    
    def __init__(self, user_id: int, form_id: int, **kwargs):
        message = f"User {user_id} does not have access to onboarding form {form_id}"
        super().__init__(message, **kwargs)
        self.user_id = user_id
        self.form_id = form_id


class FormResponseProcessingError(ClientOnboardingError):
    """Raised when form response processing fails."""
    
    def __init__(self, response_id: str, processing_stage: str, reason: str, **kwargs):
        message = f"Form response processing failed at stage '{processing_stage}' for response {response_id}: {reason}"
        super().__init__(message, **kwargs)
        self.response_id = response_id
        self.processing_stage = processing_stage
        self.reason = reason


class DatabaseOperationError(ClientOnboardingError):
    """Raised when database operations fail in the onboarding context."""
    
    def __init__(self, operation: str, entity: str, reason: str, **kwargs):
        message = f"Database operation '{operation}' failed for entity '{entity}': {reason}"
        super().__init__(message, **kwargs)
        self.operation = operation
        self.entity = entity
        self.reason = reason


class ConfigurationError(ClientOnboardingError):
    """Raised when configuration validation fails."""
    
    def __init__(self, config_key: str, issue: str, **kwargs):
        message = f"Configuration error for key '{config_key}': {issue}"
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.issue = issue


# Webhook Retry Exceptions
class WebhookRetryError(WebhookConfigurationError):
    """Base exception for webhook retry operations."""
    
    def __init__(self, webhook_id: str, reason: str, **kwargs):
        message = f"Webhook retry failed for {webhook_id}: {reason}"
        super().__init__(message, **kwargs)
        self.webhook_id = webhook_id
        self.reason = reason


class WebhookRetryPolicyViolationError(WebhookRetryError):
    """Raised when retry policy constraints are violated."""
    
    def __init__(self, webhook_id: str, policy_violation: str, **kwargs):
        reason = f"Retry policy violation: {policy_violation}"
        super().__init__(webhook_id, reason, **kwargs)
        self.policy_violation = policy_violation


class WebhookRetryExecutionError(WebhookRetryError):
    """Raised when retry execution fails."""
    
    def __init__(self, webhook_id: str, execution_error: str, **kwargs):
        reason = f"Retry execution error: {execution_error}"
        super().__init__(webhook_id, reason, **kwargs)
        self.execution_error = execution_error


class WebhookMaxRetriesExceededError(WebhookRetryError):
    """Raised when maximum retry attempts are exceeded."""
    
    def __init__(self, webhook_id: str, max_attempts: int, current_attempts: int, **kwargs):
        reason = f"Maximum retry attempts exceeded: {current_attempts}/{max_attempts}"
        super().__init__(webhook_id, reason, **kwargs)
        self.max_attempts = max_attempts
        self.current_attempts = current_attempts


class WebhookRetryDurationExceededError(WebhookRetryError):
    """Raised when maximum retry duration is exceeded."""
    
    def __init__(self, webhook_id: str, max_duration_hours: int, actual_duration_hours: float, **kwargs):
        reason = f"Maximum retry duration exceeded: {actual_duration_hours:.1f}h/{max_duration_hours}h"
        super().__init__(webhook_id, reason, **kwargs)
        self.max_duration_hours = max_duration_hours
        self.actual_duration_hours = actual_duration_hours


class WebhookPermanentlyDisabledError(WebhookRetryError):
    """Raised when webhook is permanently disabled due to failure conditions."""
    
    def __init__(self, webhook_id: str, disable_reason: str, status_code: Optional[int] = None, **kwargs):
        reason = f"Webhook permanently disabled: {disable_reason}"
        if status_code:
            reason += f" (status code: {status_code})"
        super().__init__(webhook_id, reason, **kwargs)
        self.disable_reason = disable_reason
        self.status_code = status_code


class WebhookRetryQueueError(WebhookRetryError):
    """Raised when retry queue operations fail."""
    
    def __init__(self, webhook_id: str, queue_operation: str, reason: str, **kwargs):
        error_reason = f"Retry queue {queue_operation} failed: {reason}"
        super().__init__(webhook_id, error_reason, **kwargs)
        self.queue_operation = queue_operation 