"""
API Schemas for Client Onboarding

Pydantic models for request/response validation in the client onboarding context.
"""

# Import submodules for namespace access
from src.contexts.client_onboarding.core.adapters.api_schemas import (
    auth,
    commands,
    queries,
    responses,
    webhook,
)

# Common imports for convenience
from src.contexts.client_onboarding.core.adapters.api_schemas.commands import (
    ApiDeleteOnboardingForm,
    ApiProcessWebhook,
    ApiSetupOnboardingForm,
    ApiUpdateWebhookUrl,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.queries import (
    BulkResponseQueryRequest,
    BulkResponseQueryResponse,
    ResponseQueryResponse,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.webhook import (
    TypeFormWebhookPayload,
    WebhookValidationResult,
)

__all__ = [
    # Submodules
    "responses",
    "commands",
    "queries",
    "webhook",
    "auth",
    # Common imports
    "ApiSetupOnboardingForm",
    "ApiUpdateWebhookUrl",
    "ApiDeleteOnboardingForm",
    "ApiProcessWebhook",
    "BulkResponseQueryRequest",
    "BulkResponseQueryResponse",
    "ResponseQueryResponse",
    "TypeFormWebhookPayload",
    "WebhookValidationResult",
]
