"""AWS Lambda handler for copying a meal."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_copy_meal import (
    ApiCopyMeal,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.shared_kernel.middleware.auth.authentication import (
    recipes_aws_auth_middleware,
)
from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import generate_correlation_id

from ..api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.copy_meal",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="copy_meal_exception_handler",
        logger_name="recipes_catalog.copy_meal.errors",
    ),
    timeout=30.0,
    name="copy_meal_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /meals/copy for meal duplication.

    Request:
        Body: ApiCopyMeal schema with source meal details
        Auth: AWS Cognito JWT with MANAGE_MEALS permission

    Responses:
        201: Meal copied successfully with meal_id
        400: Invalid request body or missing permissions
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to copy meal
        500: Internal server error (handled by middleware)

    Idempotency:
        No. Each call creates a new copy with unique ID.

    Notes:
        Maps to CopyMeal command and translates errors to HTTP codes.
        Requires MANAGE_MEALS permission.
        Creates new meal instance based on source meal.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract and parse request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse and validate request body using Pydantic model
    api = ApiCopyMeal.model_validate_json(raw_body)

    # Business context: Permission validation for meal copying
    if not current_user.has_permission(Permission.MANAGE_MEALS):
        error_message = "User does not have enough privileges to copy meal"
        raise PermissionError(error_message)

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Copy meal through message bus
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": API_headers,
        "body": json.dumps(
            {"message": "Meal copied successfully", "meal_id": cmd.meal_id}
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for meal copying.

    Args:
        event: AWS Lambda event with HTTP request details
        context: AWS Lambda execution context

    Returns:
        HTTP response with status code, headers, and body

    Notes:
        Generates correlation ID and delegates to async handler.
        Wraps async execution in anyio runtime.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
