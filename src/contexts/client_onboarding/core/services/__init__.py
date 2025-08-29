"""
Client Onboarding Services

Structured service layout:
- webhooks: webhook manager, processor, security
- integrations.typeform: Typeform client and helpers
- uow: Unit of Work for DB access

This package maintains backward-compatible import shims for existing paths.
"""

from src.contexts.client_onboarding.core.services.integrations.typeform.client import (
    FormInfo,
    RateLimitValidator,
    TypeFormClient,
    WebhookInfo,
    create_typeform_client,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import (
    TypeformUrlParser,
)
from src.contexts.client_onboarding.core.services.webhooks.manager import (
    WebhookManager,
    create_webhook_manager,
)
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookProcessor,
    process_typeform_webhook,
)
from src.contexts.client_onboarding.core.services.webhooks.security import (
    WebhookSecurityVerifier,
    verify_typeform_webhook,
)

__all__ = [
    "FormInfo",
    "RateLimitValidator",
    "TypeFormClient",
    "TypeformUrlParser",
    "WebhookInfo",
    "WebhookManager",
    "WebhookProcessor",
    "WebhookSecurityVerifier",
    "create_typeform_client",
    "create_webhook_manager",
    "process_typeform_webhook",
    "verify_typeform_webhook",
]
