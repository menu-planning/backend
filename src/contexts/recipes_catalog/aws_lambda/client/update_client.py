import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_update_client import (
    ApiUpdateClient,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
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
from src.contexts.shared_kernel.middleware.lambda_helpers import LambdaHelpers
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
        logger_name="recipes_catalog.update_client",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="update_client_exception_handler",
        logger_name="recipes_catalog.update_client.errors",
    ),
    timeout=30.0,
    name="update_client_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle PUT /clients/{client_id} for client updates.

    Request:
        Path: client_id (UUID v4) - client identifier
        Body: ApiClient schema with complete client data
        Auth: AWS Cognito JWT with MANAGE_CLIENTS permission

    Responses:
        200: Client updated successfully
        400: Invalid request body, missing client ID, or client not found
        401: Unauthorized (handled by middleware)
        403: Insufficient permissions to update client
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same data produce same result.

    Notes:
        Maps to UpdateClient command and translates errors to HTTP codes.
        Requires MANAGE_CLIENTS permission.
        Validates client exists before update.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract client ID from path parameters
    client_id = LambdaHelpers.extract_path_parameter(event, "client_id")
    if not client_id:
        error_message = "Client ID is required"
        raise ValueError(error_message)

    # Extract and parse request body
    raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required"
        raise ValueError(error_message)

    # Parse and validate request body using Pydantic model
    api_client_from_request = ApiClient.model_validate_json(raw_body)

    # Business context: Check if client exists and validate permissions
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            existing_client = await uow.clients.get(client_id)
        except EntityNotFoundError as err:
            error_message = f"Client {client_id} not found"
            raise ValueError(error_message) from err

        # Business context: Permission validation for client update
        if not (
            current_user.has_permission(Permission.MANAGE_CLIENTS)
            or current_user.id == existing_client.author_id
        ):
            error_message = "User does not have enough privileges to update client"
            raise PermissionError(error_message)

        # Convert existing domain client to ApiClient for comparison
        existing_api_client = ApiClient.from_domain(existing_client)

        # Create ApiUpdateClient using from_api_client with new client and old client
        api = ApiUpdateClient.from_api_client(
            api_client=api_client_from_request,
            old_api_client=existing_api_client,
        )

    # Convert to domain command
    cmd = api.to_domain()

    # Business context: Update client through message bus
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": json.dumps({"message": "Client updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for client updates.

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
