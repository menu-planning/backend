"""AWS Lambda handler for creating a meal."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import (
    ApiCreateMeal,
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

from ..cors_headers import CORS_headers

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.create_meal",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="create_meal_exception_handler",
        logger_name="recipes_catalog.create_meal.errors",
    ),
    timeout=30.0,
    name="create_meal_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /meals for meal creation.

    Request:
        Body: ApiCreateMeal schema with meal details and author_id
        Auth: AWS Cognito JWT with MANAGE_MEALS permission or author_id match

    Responses:
        201: Meal created successfully with meal_id
        400: Invalid request body or missing permissions
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        No. Each call creates a new meal with unique ID.

    Notes:
        Maps to CreateMeal command and translates errors to HTTP codes.
        Requires MANAGE_MEALS permission or user must be the author.
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
    api = ApiCreateMeal.model_validate_json(raw_body)

    # Business context: Permission validation for meal creation
    if not (
        current_user.has_permission(Permission.MANAGE_MEALS)
        or current_user.id == api.author_id
    ):
        error_message = "User does not have enough privileges to create meal"
        raise PermissionError(error_message)

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Meal creation through message bus
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps(
            {"message": "Meal created successfully", "meal_id": cmd.meal_id}
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for meal creation.

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
