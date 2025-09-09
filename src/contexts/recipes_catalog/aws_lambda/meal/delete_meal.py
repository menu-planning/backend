"""AWS Lambda handler for deleting a meal."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_delete_meal import (
    ApiDeleteMeal,
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
from src.contexts.shared_kernel.middleware.lambda_helpers import LambdaHelpers
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
        logger_name="recipes_catalog.delete_meal",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="delete_meal_exception_handler",
        logger_name="recipes_catalog.delete_meal.errors",
    ),
    timeout=30.0,
    name="delete_meal_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle DELETE /meals/{meal_id} for meal deletion.

    Request:
        Path: meal_id (UUID v4) - meal identifier
        Auth: AWS Cognito JWT with MANAGE_MEALS permission

    Responses:
        200: Meal deleted successfully
        400: Missing or invalid meal ID
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to delete meal
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result (meal already deleted).

    Notes:
        Maps to DeleteMeal command and translates errors to HTTP codes.
        Requires MANAGE_MEALS permission.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract meal ID from path parameters
    meal_id = LambdaHelpers.extract_path_parameter(event, "meal_id")
    if not meal_id:
        error_message = "Meal ID is required"
        raise ValueError(error_message)

    # Business context: Permission validation for meal deletion
    if not current_user.has_permission(Permission.MANAGE_MEALS):
        error_message = "User does not have enough privileges to delete meal"
        raise PermissionError(error_message)

    # Business context: Delete meal through message bus
    api_delete_meal = ApiDeleteMeal(meal_id=meal_id)
    cmd = api_delete_meal.to_domain()
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": json.dumps({"message": "Meal deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for meal deletion.

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
