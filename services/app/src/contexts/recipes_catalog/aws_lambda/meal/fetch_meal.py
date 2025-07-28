from typing import Any

import anyio
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_filter import ApiMealFilter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

MealListAdapter = TypeAdapter(list[ApiMeal])

@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for meals.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication and get user object for filtering
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, current_user = auth_result

    filters = LambdaHelpers.process_query_filters(
        event,
        ApiMealFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at"
    )
    
    # Apply user-specific tag filtering for meals
    if current_user:
        if filters.get("tags"):
            filters["tags"] = [i+(current_user.id,) for i in filters["tags"]]
        if filters.get("tags_not_exists"):
            filters["tags_not_exists"] = [i+(current_user.id,) for i in filters["tags_not_exists"]]

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Query execution with final filters
        logger.debug(f"Querying meals with filters: {filters}")
        result = await uow.meals.query(filter=filters)
    
    # Convert domain meals to API meals with validation error handling
    api_meals = []
    conversion_errors = 0
    
    for i, meal in enumerate(result):
        try:
            api_meal = ApiMeal.from_domain(meal)
            api_meals.append(api_meal)
        except Exception as e:
            conversion_errors += 1
            logger.warning(
                f"Failed to convert meal to API format - Meal index: {i}, "
                f"Meal ID: {getattr(meal, 'id', 'unknown')}, Error: {str(e)}"
            )
            # Continue processing other meals instead of failing completely
    
    if conversion_errors > 0:
        logger.warning(f"Meal conversion completed with {conversion_errors} errors out of {len(result)} total meals")
    
    # Serialize API meals with validation error handling
    try:
        response_body = MealListAdapter.dump_json(api_meals)
        logger.debug(f"Successfully serialized {len(api_meals)} meals")
    except Exception as e:
        logger.error(f"Failed to serialize meal list to JSON: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during response serialization"}',
        }

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)