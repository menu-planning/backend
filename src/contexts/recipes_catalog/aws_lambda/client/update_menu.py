import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_update_menu import (
    ApiUpdateMenu,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import (
    ApiMenu,
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
        logger_name="recipes_catalog.update_menu",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="update_menu_exception_handler",
        logger_name="recipes_catalog.update_menu.errors",
    ),
    timeout=30.0,
    name="update_menu_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle PUT /menus for menu updates.

    Request:
        Body: ApiMenu schema with complete menu data
        Auth: AWS Cognito JWT with MANAGE_MENUS permission

    Responses:
        200: Menu updated successfully
        400: Invalid request body or menu not found
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to update menu
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same data produce same result.

    Notes:
        Maps to UpdateMenu command and translates errors to HTTP codes.
        Requires MANAGE_MENUS permission.
        Validates menu exists before update.
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
    api_menu_from_request = ApiMenu.model_validate_json(raw_body)

    # Business context: Check if menu exists and validate permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            existing_menu = await uow.menus.get(api_menu_from_request.id)
        except EntityNotFoundError as err:
            error_message = f"Menu {api_menu_from_request.id} not found"
            raise ValueError(error_message) from err

        # Business context: Permission validation for menu update
        if not (
            current_user.has_permission(Permission.MANAGE_MENUS)
            or current_user.id == existing_menu.author_id
        ):
            error_message = "User does not have enough privileges to update menu"
            raise PermissionError(error_message)

        # Convert existing domain menu to ApiMenu for comparison
        existing_api_menu = ApiMenu.from_domain(existing_menu)

        # Create ApiUpdateMenu using from_api_menu with new menu and old menu
        api = ApiUpdateMenu.from_api_menu(
            api_menu=api_menu_from_request,
            old_api_menu=existing_api_menu,
        )

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Update menu through message bus
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": json.dumps({"message": "Menu updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for menu updates.

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
