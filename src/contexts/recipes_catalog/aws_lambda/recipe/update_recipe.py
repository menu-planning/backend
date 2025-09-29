"""AWS Lambda handler for updating a recipe by id."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import get_app_settings
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import (
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
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
        logger_name="recipes_catalog.update_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=get_app_settings().enviroment == "development",
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
    """Handle PUT /recipes/{id} for recipe updates.

    Request:
        Path: id (UUID v4) - recipe identifier
        Body: ApiRecipe schema with complete recipe data
        Auth: AWS Cognito JWT with MANAGE_RECIPES permission or author_id match

    Responses:
        200: Recipe updated successfully
        400: Invalid request body, missing recipe ID, or recipe not found
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to update recipe
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same data produce same result.

    Notes:
        Maps to UpdateRecipe command and translates errors to HTTP codes.
        Requires MANAGE_RECIPES permission or user must be the author.
        Validates recipe exists before update.
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
    api_recipe_from_request = ApiRecipe.model_validate_json(raw_body)

    # Business context: Check if recipe exists and validate permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
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
        "headers": API_headers,
        "body": json.dumps({"message": "Recipe updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for recipe updates.

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
