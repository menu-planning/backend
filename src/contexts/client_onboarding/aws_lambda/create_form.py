"""Create form Lambda handler for client onboarding.

Lambda endpoint for creating new onboarding forms with proper authorization
and validation.
"""

import json
from typing import TYPE_CHECKING, Any

from src.config.app_config import get_app_settings
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_setup_onboarding_form import (
    ApiSetupOnboardingForm,
)
from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
)

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.shared_kernel.middleware.auth.authentication import (
    client_onboarding_aws_auth_middleware,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import generate_correlation_id

from .shared.api_headers import API_headers

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="client_onboarding.create_form",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=get_app_settings().enviroment == "development",
    ),
    client_onboarding_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="create_form_exception_handler",
        logger_name="client_onboarding.create_form.errors",
    ),
    timeout=30.0,
    name="create_form_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /forms for creating new onboarding forms.

    Request:
        Path: N/A
        Query: N/A
        Body: ApiSetupOnboardingForm (JSON with typeform_id and webhook_url)
        Auth: AWS authentication middleware (provides _auth_context)

    Responses:
        201: Form setup initiated successfully
        400: Invalid request body or missing required fields
        401: Unauthorized (authentication required)
        500: Internal server error

    Idempotency:
        No. Each call creates a new form.

    Notes:
        Maps to SetupOnboardingForm command via MessageBus.
        Cross-cutting concerns handled by middleware: auth, logging, error handling, CORS.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Parse and validate request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required and must be a non-empty string"
        raise ValueError(error_message)

    api_command = ApiSetupOnboardingForm.model_validate_json(raw_body)

    # Execute business logic
    bus: MessageBus = container.bootstrap()
    cmd = api_command.to_domain(user_id=current_user.id)
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": API_headers,
        "body": json.dumps(
            {
                "message": "Form setup initiated successfully",
                "details": {
                    "form_type": api_command.typeform_id,
                    "user_id": str(current_user.id),
                },
            }
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for create form handler.

    Args:
        event: AWS Lambda event dictionary
        context: AWS Lambda context object

    Returns:
        Dict containing statusCode, headers, and body for Lambda response
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
