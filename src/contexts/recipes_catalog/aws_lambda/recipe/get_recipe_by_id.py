from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities import (
    api_recipe,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundError,
)
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

# Import the API schema class
ApiRecipe = api_recipe.ApiRecipe


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.get_recipe_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="get_recipe_by_id_exception_handler",
        logger_name="recipes_catalog.get_recipe_by_id.errors",
    ),
    timeout=30.0,
    name="get_recipe_by_id_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific recipe by id.

    This handler focuses purely on business logic. All cross-cutting concerns
    are handled by the unified middleware:
    - Authentication: AuthenticationMiddleware provides event["_auth_context"]
    - Logging: StructuredLoggingMiddleware handles request/response logging
    - Error Handling: ExceptionHandlerMiddleware catches and formats all errors
    - CORS: Handled automatically by the middleware system
    """
    # Extract recipe ID from path parameters
    recipe_id = event.get("pathParameters", {}).get("id")

    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Recipe retrieval by ID
        try:
            recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundError as err:
            error_message = f"Recipe {recipe_id} not in database"
            raise ValueError(error_message) from err

    # Convert domain recipe to API recipe
    api = ApiRecipe.from_domain(recipe)

    # Serialize API recipe
    response_body = api.model_dump_json()

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
