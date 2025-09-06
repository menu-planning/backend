"""AWS Lambda handler for copying a recipe between meals."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands import (
    api_copy_recipe,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
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

from ..cors_headers import CORS_headers

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()

# Import the API schema class
ApiCopyRecipe = api_copy_recipe.ApiCopyRecipe


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.copy_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="copy_recipe_exception_handler",
        logger_name="recipes_catalog.copy_recipe.errors",
    ),
    timeout=30.0,
    name="copy_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /recipes/copy for recipe duplication.

    Request:
        Body: ApiCopyRecipe schema with source recipe details and target user_id
        Auth: AWS Cognito JWT with MANAGE_RECIPES permission or user_id match

    Responses:
        201: Recipe copied successfully
        400: Invalid request body or missing permissions
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to copy recipe
        500: Internal server error (handled by middleware)

    Idempotency:
        No. Each call creates a new copy with unique ID.

    Notes:
        Maps to CopyRecipe command and translates errors to HTTP codes.
        Requires MANAGE_RECIPES permission or user must be the target.
        Creates new recipe instance based on source recipe.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract and parse request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse and validate request body using Pydantic model
    try:
        api = ApiCopyRecipe.model_validate_json(raw_body)
    except Exception as e:
        error_message = f"Invalid recipe copy data: {e!s}"
        raise ValueError(error_message) from e

    # Business context: Permission validation for recipe copying
    if not (
        current_user.has_permission(Permission.MANAGE_RECIPES)
        or api.user_id == current_user.id
    ):
        error_message = "User does not have enough privileges to copy this recipe"
        raise PermissionError(error_message)

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Recipe copying through message bus
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe copied successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for recipe copying.

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
