"""Update form Lambda handler for client onboarding.

Lambda endpoint for updating existing onboarding forms with proper authorization
and validation.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_update_webhook_url import (
    ApiUpdateWebhookUrl,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.form_management import (
    FormManagementResponse,
    FormOperationType,
)
from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
)

if TYPE_CHECKING:
    from src.contexts.client_onboarding.core.services.uow import UnitOfWork
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

from .shared.cors_headers import CORS_headers

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name='client_onboarding.update_form',
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    client_onboarding_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name='update_form_exception_handler',
        logger_name='client_onboarding.update_form.errors',
    ),
    timeout=30.0,
    name='update_form_handler',
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle PATCH /forms/{form_id} for updating onboarding forms.

    Request:
        Path: form_id (integer, required)
        Query: N/A
        Body: ApiUpdateWebhookUrl (JSON with new_webhook_url)
        Auth: AWS authentication middleware (provides _auth_context)

    Responses:
        200: FormManagementResponse with update details
        400: Invalid form_id, request body, or missing path parameter
        401: Unauthorized (authentication required)
        404: Form not found or user lacks permission
        500: Internal server error

    Idempotency:
        Yes. Key: form_id + user_id + new_webhook_url. Duplicate calls have no effect.

    Notes:
        Updates form fields through UnitOfWork with ownership validation.
        Cross-cutting concerns handled by middleware: auth, logging, error handling, CORS.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event['_auth_context']
    current_user = auth_context.user_object

    # Get form ID from path parameters
    form_id = event.get('pathParameters', {}).get('form_id')
    if not form_id:
        error_message = 'Form ID is required in path parameters'
        raise ValueError(error_message)

    form_id = int(form_id)

    # Parse and validate request body (new webhook URL)
    raw_body = event.get('body', '')
    if not isinstance(raw_body, str) or not raw_body.strip():
        raw_body = '{}'

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
            updated_fields.append('webhook_url')

        # Status updates are not part of the API command in this endpoint
        existing_form.updated_at = datetime.now(UTC)
        updated_fields.append('updated_at')

        await uow.commit()

        # Create success response
        response = FormManagementResponse(
            success=True,
            operation=FormOperationType.UPDATE,
            form_id=form_id,
            message=f"Form {form_id} updated successfully",
            created_form_id=None,
            updated_fields=updated_fields,
            webhook_status='updated',
            operation_timestamp=datetime.now(UTC),
            execution_time_ms=None,
            error_code=None,
            error_details=None,
            warnings=[],
        )

    return {
        'statusCode': 200,
        'headers': CORS_headers,
        'body': response.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for update form handler.

    Args:
        event: AWS Lambda event dictionary
        context: AWS Lambda context object

    Returns:
        Dict containing statusCode, headers, and body for Lambda response
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
