from typing import TYPE_CHECKING, Any

import anyio
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities import (
    api_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_filter import (  # noqa: E501
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.contexts.shared_kernel.middleware.auth.authentication import (
    recipes_aws_auth_middleware,
)
from src.contexts.shared_kernel.middleware.decorators import async_endpoint_handler
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import generate_correlation_id

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()

# Import the API schema classes
ApiRecipe = api_recipe.ApiRecipe
RecipeListAdapter = TypeAdapter(list[ApiRecipe])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.fetch_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_recipe_exception_handler",
        logger_name="recipes_catalog.fetch_recipe.errors",
    ),
    timeout=30.0,
    name="fetch_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for recipes.

    This handler focuses purely on business logic. All cross-cutting concerns
    are handled by the unified middleware:
    - Authentication: AuthenticationMiddleware provides event["_auth_context"]
    - Logging: StructuredLoggingMiddleware handles request/response logging
    - Error Handling: ExceptionHandlerMiddleware catches and formats all errors
    - CORS: Handled automatically by the middleware system
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiRecipeFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at",
    )

    # Apply user-specific tag filtering for recipes
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
        result = await uow.recipes.query(filters=filters)

    # Convert domain recipes to API recipes
    api_recipes = []
    for recipe in result:
        api_recipe = ApiRecipe.from_domain(recipe)
        api_recipes.append(api_recipe)

    # Serialize API recipes
    response_body = RecipeListAdapter.dump_json(api_recipes)

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
