"""
Client Onboarding Context

Handles TypeForm integration for automated client onboarding processes.
Provides services for form management, webhook processing, and client data capture.
"""

# Core Components
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_delete_onboarding_form import (
    ApiDeleteOnboardingForm,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_process_webhook import (
    ApiProcessWebhook,
)

# API Schemas - Commands
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_setup_onboarding_form import (
    ApiSetupOnboardingForm,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_update_webhook_url import (
    ApiUpdateWebhookUrl,
)

# API Schemas - Queries
from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    BulkResponseQueryRequest,
    BulkResponseQueryResponse,
    ResponseQueryResponse,
)
from src.contexts.client_onboarding.core.adapters.repositories.form_response_repository import (
    FormResponseRepo,
)

# Repositories
from src.contexts.client_onboarding.core.adapters.repositories.onboarding_form_repository import (
    OnboardingFormRepo,
)
from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.domain.commands.delete_onboarding_form import (
    DeleteOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.domain.commands.process_webhook import (
    ProcessWebhookCommand,
)

# Domain Commands
from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import (
    SetupOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.domain.commands.update_webhook_url import (
    UpdateWebhookUrlCommand,
)
from src.contexts.client_onboarding.core.domain.models.form_response import FormResponse

# Domain Models
from src.contexts.client_onboarding.core.domain.models.onboarding_form import (
    OnboardingForm,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.client import (
    TypeFormClient,
    create_typeform_client,
)

# Services
from src.contexts.client_onboarding.core.services.webhooks.manager import (
    WebhookManager,
    create_webhook_manager,
)
from src.contexts.client_onboarding.core.services.webhooks.processor import (
    WebhookProcessor,
    process_typeform_webhook,
)

__version__ = "1.0.0"

__all__ = [
    # Core
    "Container",
    # API Schemas - Commands
    "ApiSetupOnboardingForm",
    "ApiUpdateWebhookUrl",
    "ApiDeleteOnboardingForm",
    "ApiProcessWebhook",
    # API Schemas - Queries
    "BulkResponseQueryRequest",
    "BulkResponseQueryResponse",
    "ResponseQueryResponse",
    # Domain Models
    "OnboardingForm",
    "FormResponse",
    # Domain Commands
    "SetupOnboardingFormCommand",
    "UpdateWebhookUrlCommand",
    "DeleteOnboardingFormCommand",
    "ProcessWebhookCommand",
    # Services
    "WebhookManager",
    "create_webhook_manager",
    "WebhookProcessor",
    "process_typeform_webhook",
    "TypeFormClient",
    "create_typeform_client",
    # Repositories
    "OnboardingFormRepo",
    "FormResponseRepo",
]
