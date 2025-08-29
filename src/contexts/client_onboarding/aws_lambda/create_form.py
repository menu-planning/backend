"""
Create Form Lambda Handler

Lambda endpoint for creating new onboarding forms with proper authorization and
validation.
"""

from typing import TYPE_CHECKING, Any

from src.contexts.shared_kernel.middleware.decorators import async_endpoint_handler

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio

from src.contexts.client_onboarding.aws_lambda.shared import CORS_headers
from src.contexts.client_onboarding.core import Container
from src.contexts.client_onboarding.core.adapters import (
    ApiSetupOnboardingForm,
)
from src.contexts.shared_kernel.adapters.api_schemas.responses.base_response import (
    CreatedResponse,
    MessageResponse,
)
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

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="client_onboarding.create_form",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
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
    """
    Lambda function handler to create a new onboarding form.

    This handler focuses purely on business logic. All cross-cutting concerns
    are handled by the unified middleware:
    - Authentication: AuthenticationMiddleware provides event["_auth_context"]
    - Logging: StructuredLoggingMiddleware handles request/response logging
    - Error Handling: ExceptionHandlerMiddleware catches and formats all errors
    - CORS: Handled automatically by the middleware system

    Args:
        event: AWS Lambda event dictionary with _auth_context added by middleware
        context: AWS Lambda context object
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

    # Create success response
    message_response = MessageResponse(
        message="Form setup initiated successfully",
        details={
            "form_type": api_command.typeform_id,
            "user_id": str(current_user.id),
        },
    )

    success_response = CreatedResponse[MessageResponse](
        status_code=201, headers=CORS_headers, body=message_response
    )

    return {
        "statusCode": success_response.status_code,
        "headers": success_response.headers,
        "body": success_response.body.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda function handler entry point for creating forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
