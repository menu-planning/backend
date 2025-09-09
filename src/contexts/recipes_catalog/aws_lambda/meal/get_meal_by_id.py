"""AWS Lambda handler for retrieving a meal by id."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
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
from src.logging.logger import StructlogFactory, generate_correlation_id

from ..api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

logger = StructlogFactory.get_logger(__name__)

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.get_meal_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="get_meal_by_id_exception_handler",
        logger_name="recipes_catalog.get_meal_by_id.errors",
    ),
    timeout=30.0,
    name="get_meal_by_id_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /meals/{meal_id} for meal retrieval.

    Request:
        Path: meal_id (UUID v4) - meal identifier
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: Meal found and returned as JSON
        400: Missing or invalid meal ID
        404: Meal not found
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result.

    Notes:
        Maps to Meal repository get() method and translates errors to HTTP codes.
        No special permissions required for read access.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract meal ID from path parameters
    meal_id = LambdaHelpers.extract_path_parameter(event, "id")
    if not meal_id:
        error_message = "Meal ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Get meal by ID
        meal = await uow.meals.get(meal_id)

    if not meal:
        error_message = "Meal not found"
        raise ValueError(error_message)

    # Convert domain meal to API meal
    api_meal = ApiMeal.from_domain(meal)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": api_meal.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for meal retrieval.

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
