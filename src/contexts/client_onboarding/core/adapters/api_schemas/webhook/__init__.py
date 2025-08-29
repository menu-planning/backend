"""
Webhook API Schemas

Pydantic models for webhook payload validation and processing.
"""

from src.contexts.client_onboarding.core.adapters.api_schemas.webhook.typeform_webhook_payload import (
    FieldAnswer,
    FieldChoice,
    FieldDefinition,
    FieldType,
    FormDefinition,
    FormResponse,
    TypeFormWebhookPayload,
    WebhookEventType,
    WebhookHeaders,
    WebhookProcessingContext,
    WebhookSignatureValidation,
    WebhookValidationResult,
)

__all__ = [
    "FieldAnswer",
    "FieldChoice",
    "FieldDefinition",
    "FieldType",
    "FormDefinition",
    "FormResponse",
    "TypeFormWebhookPayload",
    "WebhookEventType",
    "WebhookHeaders",
    "WebhookProcessingContext",
    "WebhookSignatureValidation",
    "WebhookValidationResult",
]
