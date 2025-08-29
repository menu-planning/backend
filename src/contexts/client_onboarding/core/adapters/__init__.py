"""
Client Onboarding Adapters

Contains database repositories and external service adapters.
"""

# API Schemas - Commands
from src.contexts.client_onboarding.core.adapters.api_schemas.commands import (
    ApiDeleteOnboardingForm,
    ApiProcessWebhook,
    ApiSetupOnboardingForm,
    ApiUpdateWebhookUrl,
)

# API Schemas - Queries
from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    BulkResponseQueryRequest,
    BulkResponseQueryResponse,
    ResponseQueryResponse,
)

# API Schemas - Responses
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_management import (
    FormManagementResponse,
    FormOperationType,
)

# API Schemas - Webhook
from src.contexts.client_onboarding.core.adapters.api_schemas.webhook import (
    TypeFormWebhookPayload,
    WebhookValidationResult,
)

# External Providers
from src.contexts.client_onboarding.core.adapters.external_providers.iam import (
    IAMProvider,
)

# Middleware
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_api_logging_middleware,
)
from src.contexts.client_onboarding.core.adapters.repositories.form_response_repository import (
    FormResponseRepo,
)

# Repositories
from src.contexts.client_onboarding.core.adapters.repositories.onboarding_form_repository import (
    OnboardingFormRepo,
)

# Security
from src.contexts.client_onboarding.core.adapters.security.webhook_signature_validator import (
    WebhookSignatureValidator,
    validate_typeform_webhook_signature,
)

# Validators
from src.contexts.client_onboarding.core.adapters.validators.ownership_validator import (
    FormOwnershipValidator,
)

__all__ = [
    # API Schemas - Commands
    "ApiSetupOnboardingForm",
    "ApiUpdateWebhookUrl",
    "ApiDeleteOnboardingForm",
    "ApiProcessWebhook",
    # API Schemas - Queries
    "BulkResponseQueryRequest",
    "BulkResponseQueryResponse",
    "ResponseQueryResponse",
    # API Schemas - Responses
    "FormOperationType",
    "FormManagementResponse",
    # API Schemas - Webhook
    "TypeFormWebhookPayload",
    "WebhookValidationResult",
    # External Providers
    "IAMProvider",
    # Repositories
    "OnboardingFormRepo",
    "FormResponseRepo",
    # Middleware
    "create_api_logging_middleware",
    # Validators
    "FormOwnershipValidator",
    # Security
    "WebhookSignatureValidator",
    "validate_typeform_webhook_signature",
]
