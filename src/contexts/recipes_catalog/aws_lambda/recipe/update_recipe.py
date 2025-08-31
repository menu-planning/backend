import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands import (
    api_update_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities import (
    api_recipe,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
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

# Import the API schema classes
ApiRecipe = api_recipe.ApiRecipe
ApiUpdateRecipe = api_update_recipe.ApiUpdateRecipe


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.update_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="update_recipe_exception_handler",
        logger_name="recipes_catalog.update_recipe.errors",
    ),
    timeout=30.0,
    name="update_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to update a recipe by its id.

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
        error_message = "Recipe ID is required in path parameters"
        raise ValueError(error_message)

    # Extract and parse request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse and validate request body as a complete recipe using ApiRecipe
    try:
        # Parse raw_body as complete recipe
        api_recipe_from_request = ApiRecipe.model_validate_json(raw_body)
    except Exception as e:
        error_message = f"Invalid recipe data: {e!s}"
        raise ValueError(error_message) from e

    # Business context: Check if recipe exists and validate permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            existing_recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundError as err:
            error_message = f"Recipe {recipe_id} not found"
            raise ValueError(error_message) from err

        # Business context: Permission validation for recipe update
        if not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or current_user.id == existing_recipe.author_id
        ):
            error_message = "User does not have enough privileges to update this recipe"
            raise PermissionError(error_message)

        # Convert existing domain recipe to ApiRecipe for comparison
        existing_api_recipe = ApiRecipe.from_domain(existing_recipe)

        # Create ApiUpdateRecipe using from_api_recipe with new recipe and old recipe
        api_of_update_cmd = ApiUpdateRecipe.from_api_recipe(
            api_recipe=api_recipe_from_request,
            old_api_recipe=existing_api_recipe,
        )

    # Convert to domain command
    cmd = api_of_update_cmd.to_domain()

    # Business context: Recipe update through message bus
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
