from typing import Any

import anyio
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_filter import ApiRecipeFilter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
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

RecipeListAdapter = TypeAdapter(list[ApiRecipe])

@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for recipes.
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
        ApiRecipeFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at"
    )
    
    # Apply user-specific tag filtering for recipes
    if current_user:
        if filters.get("tags"):
            filters["tags"] = [i+(current_user.id,) for i in filters["tags"]]
        if filters.get("tags_not_exists"):
            filters["tags_not_exists"] = [i+(current_user.id,) for i in filters["tags_not_exists"]]

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Query execution with final filters
        logger.debug(f"Querying recipes with filters: {filters}")
        result = await uow.recipes.query(filter=filters)
    
    # Business context: Results summary
    logger.debug(f"Found {len(result)} recipes")

    # Convert domain recipes to API recipes with validation error handling
    api_recipes = []
    conversion_errors = 0
    
    for i, recipe in enumerate(result):
        try:
            api_recipe = ApiRecipe.from_domain(recipe)
            api_recipes.append(api_recipe)
        except Exception as e:
            conversion_errors += 1
            logger.warning(
                f"Failed to convert recipe to API format - Recipe index: {i}, "
                f"Recipe ID: {getattr(recipe, 'id', 'unknown')}, Error: {str(e)}"
            )
            # Continue processing other recipes instead of failing completely
    
    if conversion_errors > 0:
        logger.warning(f"Recipe conversion completed with {conversion_errors} errors out of {len(result)} total recipes")
    
    # Serialize API recipes with validation error handling
    try:
        response_body = RecipeListAdapter.dump_json(api_recipes)
        logger.debug(f"Successfully serialized {len(api_recipes)} recipes")
    except Exception as e:
        logger.error(f"Failed to serialize recipe list to JSON: {str(e)}")
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
