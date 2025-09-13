"""AWS Lambda handler for updating a meal."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
)
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
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.update_meal",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="update_meal_exception_handler",
        logger_name="recipes_catalog.update_meal.errors",
    ),
    timeout=30.0,
    name="update_meal_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle PUT /meals/{meal_id} for meal updates.

    Request:
        Path: meal_id (UUID v4) - meal identifier
        Body: ApiMeal schema with complete meal data
        Auth: AWS Cognito JWT with MANAGE_MEALS permission

    Responses:
        200: Meal updated successfully
        400: Invalid request body, missing meal ID, or meal not found
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to update meal
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same data produce same result.

    Notes:
        Maps to UpdateMeal command and translates errors to HTTP codes.
        Requires MANAGE_MEALS permission.
        Validates meal exists before update.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract meal ID from path parameters
    meal_id = LambdaHelpers.extract_path_parameter(event, "meal_id")
    if not meal_id:
        error_message = "Meal ID is required"
        raise ValueError(error_message)

    # Extract and parse request body
    raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse and validate request body using Pydantic model
    api_meal_from_request = ApiMeal.model_validate_json(raw_body)

    # Business context: Check if meal exists and validate permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            existing_meal = await uow.meals.get(meal_id)
        except EntityNotFoundError as err:
            error_message = f"Meal {meal_id} not found"
            raise ValueError(error_message) from err

        # Business context: Permission validation for meal update
        if not (
            current_user.has_permission(Permission.MANAGE_MEALS)
            or current_user.id == existing_meal.author_id
        ):
            error_message = "User does not have enough privileges to update meal"
            raise PermissionError(error_message)

        # Convert existing domain meal to ApiMeal for comparison
        existing_api_meal = ApiMeal.from_domain(existing_meal)

        # Create ApiUpdateMeal using from_api_meal with new meal and old meal
        api = ApiUpdateMeal.from_api_meal(
            api_meal=api_meal_from_request,
            old_api_meal=existing_api_meal,
        )

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Update meal through message bus
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": json.dumps({"message": "Meal updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for meal updates.

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
