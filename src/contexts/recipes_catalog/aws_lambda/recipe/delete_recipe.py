"""AWS Lambda handler for deleting a recipe."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import get_app_settings
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.domain.meal.commands.delete_recipe import (
    DeleteRecipe,
)
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
        logger_name="recipes_catalog.delete_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=get_app_settings().enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="delete_recipe_exception_handler",
        logger_name="recipes_catalog.delete_recipe.errors",
    ),
    timeout=30.0,
    name="delete_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle DELETE /recipes/{id} for recipe deletion.

    Request:
        Path: id (UUID v4) - recipe identifier
        Auth: AWS Cognito JWT with MANAGE_RECIPES permission or author_id match

    Responses:
        200: Recipe deleted successfully
        400: Missing or invalid recipe ID
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to delete recipe
        404: Recipe not found
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result (recipe already deleted).

    Notes:
        Maps to DeleteRecipe command and translates errors to HTTP codes.
        Requires MANAGE_RECIPES permission or user must be the author.
        Validates recipe exists before deletion.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract recipe ID from path parameters
    recipe_id = event.get("pathParameters", {}).get("id")
    if not recipe_id:
        error_message = "Recipe ID is required"
        raise ValueError(error_message)

    # Business context: Get recipe to verify existence and check permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        try:
            recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundError as err:
            error_message = "Recipe not found"
            raise ValueError(error_message) from err

    # Business context: Permission validation for recipe deletion
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or recipe.author_id == current_user.id
    ):
        error_message = "User does not have enough privileges to delete this recipe"
        raise PermissionError(error_message)

    # Business context: Recipe deletion through message bus
    cmd = DeleteRecipe(recipe_id=recipe_id)
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": json.dumps({"message": "Recipe deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for recipe deletion.

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
