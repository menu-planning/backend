"""
Client Onboarding Core Module

Contains the business logic, repositories, and services for client onboarding.
"""

# Bootstrap
# Adapters
from src.contexts.client_onboarding.core.adapters import (
    ApiSetupOnboardingForm,
    BulkResponseQueryRequest,
    BulkResponseQueryResponse,
    FormOwnershipValidator,
    IAMProvider,
    ResponseQueryResponse,
    create_api_logging_middleware,
)
from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.domain.commands import (
    DeleteOnboardingFormCommand,
    ProcessWebhookCommand,
    SetupOnboardingFormCommand,
    UpdateWebhookUrlCommand,
)

# Domain
from src.contexts.client_onboarding.core.domain.models import (
    FormResponse,
    OnboardingForm,
)

# Services
from src.contexts.client_onboarding.core.services import (
    TypeFormClient,
    WebhookManager,
    WebhookProcessor,
    create_typeform_client,
    create_webhook_manager,
    process_typeform_webhook,
)

__all__ = [
    # Bootstrap
    "Container",
    # Domain
    "OnboardingForm",
    "FormResponse",
    "SetupOnboardingFormCommand",
    "UpdateWebhookUrlCommand",
    "DeleteOnboardingFormCommand",
    "ProcessWebhookCommand",
    # Services
    "WebhookManager",
    "WebhookProcessor",
    "TypeFormClient",
    "create_webhook_manager",
    "process_typeform_webhook",
    "create_typeform_client",
    # Adapters
    "ApiSetupOnboardingForm",
    "BulkResponseQueryRequest",
    "BulkResponseQueryResponse",
    "FormOwnershipValidator",
    "IAMProvider",
    "ResponseQueryResponse",
    "create_api_logging_middleware",
]
