"""AWS Lambda handler for retrieving a recipe by id."""

from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities import (
    api_recipe,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
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

# Import the API schema class
ApiRecipe = api_recipe.ApiRecipe


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.get_recipe_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
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
    """Handle GET /recipes/{id} for recipe retrieval.

    Request:
        Path: id (UUID v4) - recipe identifier
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: Recipe found and returned as JSON
        400: Missing or invalid recipe ID
        404: Recipe not found
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result.

    Notes:
        Maps to Recipe repository get() method and translates errors to HTTP codes.
        No special permissions required for read access.
    """
    # Extract recipe ID from path parameters
    recipe_id = LambdaHelpers.extract_path_parameter(event, "id")

    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
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
        "headers": API_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for recipe retrieval.

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
