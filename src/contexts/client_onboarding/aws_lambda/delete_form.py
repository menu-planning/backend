"""
Delete Form Lambda Handler

Lambda endpoint for deleting onboarding forms with proper authorization and validation.
"""

import json
from typing import TYPE_CHECKING, Any

from src.contexts.shared_kernel.middleware.decorators import async_endpoint_handler

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus
import anyio
from src.contexts.client_onboarding.aws_lambda.shared import CORS_headers
from src.contexts.client_onboarding.core.adapters import (
    ApiDeleteOnboardingForm,
)
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

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="client_onboarding.delete_form",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    client_onboarding_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="delete_form_exception_handler",
        logger_name="client_onboarding.delete_form.errors",
    ),
    timeout=30.0,
    name="delete_form_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete an onboarding form.

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

    # Get form ID from path parameters
    form_id_raw = event.get("pathParameters", {}).get("form_id")
    if not form_id_raw:
        error_message = "Form ID is required in path parameters"
        raise ValueError(error_message)

    form_id = int(form_id_raw)

    # Execute business logic
    bus: MessageBus = container.bootstrap()
    api_cmd = ApiDeleteOnboardingForm(form_id=form_id)
    cmd = api_cmd.to_domain(user_id=current_user.id)
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Form deleted successfully",
            "details": {"form_id": form_id, "user_id": str(current_user.id)},
        }),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda function handler entry point for deleting forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
