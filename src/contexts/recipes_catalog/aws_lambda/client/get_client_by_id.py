"""AWS Lambda handler for retrieving a client by id."""

from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
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
        logger_name="recipes_catalog.get_client_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="get_client_by_id_exception_handler",
        logger_name="recipes_catalog.get_client_by_id.errors",
    ),
    timeout=30.0,
    name="get_client_by_id_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /clients/{client_id} for client retrieval.

    Request:
        Path: client_id (UUID v4) - client identifier
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: Client found and returned as JSON
        400: Missing or invalid client ID
        404: Client not found
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result.

    Notes:
        Maps to Client repository get() method and translates errors to HTTP codes.
        No special permissions required for read access.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract client ID from path parameters
    client_id = LambdaHelpers.extract_path_parameter(event, "client_id")
    if not client_id:
        error_message = "Client ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Get client by ID
        client = await uow.clients.get(client_id)

    if not client:
        error_message = "Client not found"
        raise ValueError(error_message)

    # Convert domain client to API client
    api_client = ApiClient.from_domain(client)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": api_client.model_dump_json(),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for client retrieval.

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
