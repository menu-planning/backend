"""
Client Onboarding Services

Structured service layout:
- webhooks: webhook manager, processor, security
- integrations.typeform: Typeform client and helpers
- uow: Unit of Work for DB access

This package maintains backward-compatible import shims for existing paths.
"""

from .webhooks.manager import WebhookManager, create_webhook_manager
from .webhooks.processor import WebhookProcessor, process_typeform_webhook
from .webhooks.security import WebhookSecurityVerifier, verify_typeform_webhook
from .integrations.typeform.client import (
    TypeFormClient,
    WebhookInfo,
    FormInfo,
    RateLimitValidator,
    create_typeform_client,
)
from .integrations.typeform.url_parser import TypeformUrlParser

__all__ = [
    "WebhookManager",
    "create_webhook_manager",
    "WebhookProcessor",
    "process_typeform_webhook",
    "WebhookSecurityVerifier",
    "verify_typeform_webhook",
    "TypeFormClient",
    "WebhookInfo",
    "FormInfo",
    "RateLimitValidator",
    "create_typeform_client",
    "TypeformUrlParser",
]