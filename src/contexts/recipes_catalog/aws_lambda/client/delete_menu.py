import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_delete_menu import (
    ApiDeleteMenu,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
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
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.delete_menu",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="delete_menu_exception_handler",
        logger_name="recipes_catalog.delete_menu.errors",
    ),
    timeout=30.0,
    name="delete_menu_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a menu.

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

    # Extract client ID and menu ID from path parameters
    client_id = event.get("pathParameters", {}).get("client_id")
    menu_id = event.get("pathParameters", {}).get("menu_id")

    if not client_id:
        error_message = "Client ID is required"
        raise ValueError(error_message)

    if not menu_id:
        error_message = "Menu ID is required"
        raise ValueError(error_message)

    # Business context: Permission validation for menu deletion
    if not current_user.has_permission(Permission.MANAGE_MENUS):
        error_message = "User does not have enough privileges to delete menu"
        raise PermissionError(error_message)

    # Business context: Delete menu through message bus
    api_delete_menu = ApiDeleteMenu(menu_id=menu_id)
    cmd = api_delete_menu.to_domain()
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Menu deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
