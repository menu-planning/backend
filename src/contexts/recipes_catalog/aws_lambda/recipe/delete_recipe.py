import json
from typing import TYPE_CHECKING, Any

import anyio

from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.domain.meal.commands.delete_recipe import (
    DeleteRecipe,
)
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


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.delete_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
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
    """
    Lambda function handler to delete a recipe.

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

    # Business context: Get recipe to verify existence and check permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
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
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
