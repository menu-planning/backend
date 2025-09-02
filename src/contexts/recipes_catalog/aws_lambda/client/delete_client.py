"""AWS Lambda handler for deleting a client."""
import json
from typing import TYPE_CHECKING, Any

import anyio
from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_delete_client import (
    ApiDeleteClient,
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

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.delete_client",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="delete_client_exception_handler",
        logger_name="recipes_catalog.delete_client.errors",
    ),
    timeout=30.0,
    name="delete_client_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle DELETE /clients/{client_id} for client deletion.

    Request:
        Path: client_id (UUID v4) - client identifier
        Auth: AWS Cognito JWT with MANAGE_CLIENTS permission

    Responses:
        200: Client deleted successfully
        400: Missing or invalid client ID
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to delete client
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result (client already deleted).

    Notes:
        Maps to DeleteClient command and translates errors to HTTP codes.
        Requires MANAGE_CLIENTS permission.
        Cascading deletion of associated menus may occur.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract client ID from path parameters
    client_id = event.get("pathParameters", {}).get("client_id")
    if not client_id:
        error_message = "Client ID is required"
        raise ValueError(error_message)

    # Business context: Permission validation for client deletion
    if not current_user.has_permission(Permission.MANAGE_CLIENTS):
        error_message = "User does not have enough privileges to delete client"
        raise PermissionError(error_message)

    # Business context: Delete client through message bus
    api_delete_client = ApiDeleteClient(client_id=client_id)
    cmd = api_delete_client.to_domain()
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Client deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for client deletion.

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
