"""
Update Form Lambda Handler

Lambda endpoint for updating existing onboarding forms with proper authorization and
validation.
"""

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.contexts.shared_kernel.middleware.decorators import async_endpoint_handler

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from src.contexts.client_onboarding.aws_lambda.shared import CORS_headers
from src.contexts.client_onboarding.core.adapters.api_schemas.commands import (
    ApiUpdateWebhookUrl,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses import (
    FormManagementResponse,
    FormOperationType,
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
        logger_name="client_onboarding.update_form",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    client_onboarding_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="update_form_exception_handler",
        logger_name="client_onboarding.update_form.errors",
    ),
    timeout=30.0,
    name="update_form_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to update an existing onboarding form.

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
    form_id = event.get("pathParameters", {}).get("form_id")
    if not form_id:
        error_message = "Form ID is required in path parameters"
        raise ValueError(error_message)

    form_id = int(form_id)

    # Parse and validate request body (new webhook URL)
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        raw_body = "{}"

    api_cmd = ApiUpdateWebhookUrl.model_validate_json(raw_body)
    # Ensure path form_id overrides body form_id
    api_cmd = ApiUpdateWebhookUrl(
        form_id=form_id, new_webhook_url=api_cmd.new_webhook_url
    )

    # Business logic: Update form through UoW
    bus: MessageBus = container.bootstrap()

    uow: UnitOfWork
    async with bus.uow as uow:
        # Get existing form and verify ownership
        existing_form = await uow.onboarding_forms.get_by_id(form_id)
        if not existing_form:
            error_message = f"Form with ID {form_id} does not exist"
            raise ValueError(error_message)

        # Check ownership
        if existing_form.user_id != current_user.id:
            error_message = (
                f"User {current_user.id} does not have permission "
                f"to modify form {form_id}"
            )
            raise ValueError(error_message)

        # Update form fields
        updated_fields = []
        if api_cmd.new_webhook_url is not None:
            existing_form.webhook_url = str(api_cmd.new_webhook_url)
            updated_fields.append("webhook_url")

        # Status updates are not part of the API command in this endpoint
        existing_form.updated_at = datetime.now(UTC)
        updated_fields.append("updated_at")

        await uow.commit()

        # Create success response
        response = FormManagementResponse(
            success=True,
            operation=FormOperationType.UPDATE,
            form_id=form_id,
            message=f"Form {form_id} updated successfully",
            created_form_id=None,
            updated_fields=updated_fields,
            webhook_status="updated",
            operation_timestamp=datetime.now(UTC),
            execution_time_ms=None,
            error_code=None,
            error_details=None,
            warnings=[],
        )

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda function handler entry point for updating forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
