"""AWS Lambda handler for creating a client in recipes catalog."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import get_app_settings
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_create_client import (
    ApiCreateClient,
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

from ..api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.create_client",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=get_app_settings().enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="create_client_exception_handler",
        logger_name="recipes_catalog.create_client.errors",
    ),
    timeout=30.0,
    name="create_client_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /clients for client creation.

    Request:
        Body: ApiCreateClient schema with client details
        Auth: AWS Cognito JWT with MANAGE_CLIENTS permission

    Responses:
        201: Client created successfully
        400: Invalid request body or missing permissions
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        No. Each call creates a new client with unique ID.

    Notes:
        Maps to CreateClient command and translates errors to HTTP codes.
        Requires MANAGE_CLIENTS permission.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract and parse request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse request body and inject author_id from authenticated user
    body_data = json.loads(raw_body)
    body_data["author_id"] = current_user.id

    # Convert back to JSON string to leverage model_validate_json's type conversions
    modified_body = json.dumps(body_data)

    # Parse and validate request body using Pydantic model
    api = ApiCreateClient.model_validate_json(modified_body)

    # Business context: Permission validation for client creation
    if not current_user.has_permission(Permission.MANAGE_CLIENTS):
        error_message = "User does not have enough privileges to create client"
        raise PermissionError(error_message)

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Create client through message bus
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": API_headers,
        "body": json.dumps({"message": "Client created successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for client creation.

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
