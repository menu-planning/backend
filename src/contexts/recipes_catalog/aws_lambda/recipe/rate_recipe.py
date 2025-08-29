import json
from typing import TYPE_CHECKING, Any

import anyio

from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands import (
    api_rate_recipe,
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
ApiRateRecipe = api_rate_recipe.ApiRateRecipe


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.rate_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="rate_recipe_exception_handler",
        logger_name="recipes_catalog.rate_recipe.errors",
    ),
    timeout=30.0,
    name="rate_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to rate a recipe.

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

    # Extract recipe ID from path parameters
    recipe_id = event.get("pathParameters", {}).get("id")
    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)

    # Extract and parse request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse request body
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON in request body: {e!s}"
        raise ValueError(error_message) from e

    # Verify recipe exists
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            await uow.recipes.get(recipe_id)
        except EntityNotFoundError as err:
            error_message = f"Recipe {recipe_id} not in database"
            raise ValueError(error_message) from err

    # Add user ID to body and create API command
    body["user_id"] = current_user.id
    api = ApiRateRecipe(rating=body)
    cmd = api.to_domain()

    # Execute rating command
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe rated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
