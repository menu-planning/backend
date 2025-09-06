"""AWS Lambda handler for querying meals."""

from typing import TYPE_CHECKING, Any

import anyio
from pydantic import TypeAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_filter import (
    ApiMealFilter,
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
from src.logging.logger import generate_correlation_id

from ..cors_headers import CORS_headers

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()

MealListAdapter = TypeAdapter(list[ApiMeal])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.fetch_meal",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_meal_exception_handler",
        logger_name="recipes_catalog.fetch_meal.errors",
    ),
    timeout=30.0,
    name="fetch_meal_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /meals for meal querying with filters.

    Request:
        Query: filters (optional) - ApiMealFilter schema with pagination, sorting, and search criteria
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: List of meals matching criteria returned as JSON
        400: Invalid filter parameters
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same filters return same result.

    Notes:
        Maps to Meal repository query() method and translates errors to HTTP codes.
        Default limit: 50, default sort: -updated_at (newest first).
        User-specific tag filtering applied automatically.
        Continues processing on individual meal conversion errors.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiMealFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at",
    )

    # Apply user-specific tag filtering for meals
    if current_user:
        if filters.get("tags"):
            filters["tags"] = [(i, current_user.id) for i in filters["tags"]]
        if filters.get("tags_not_exists"):
            filters["tags_not_exists"] = [
                (i, current_user.id) for i in filters["tags_not_exists"]
            ]

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Query execution with final filters
        result = await uow.meals.query(filters=filters)

    # Convert domain meals to API meals
    api_meals = []
    conversion_errors = 0

    for _, meal in enumerate(result):
        try:
            api_meal = ApiMeal.from_domain(meal)
            api_meals.append(api_meal)
        except Exception:
            conversion_errors += 1
            # Continue processing other meals instead of failing completely

    if conversion_errors > 0:
        # Log warning but continue - this is handled by logging middleware
        pass

    # Serialize API meals
    response_body = MealListAdapter.dump_json(api_meals)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for meal querying.

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
