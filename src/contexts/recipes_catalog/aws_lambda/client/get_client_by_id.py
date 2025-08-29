import json
from typing import TYPE_CHECKING, Any

import anyio

from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
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
        logger_name="recipes_catalog.get_client_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
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
    """
    Lambda function handler to get a client by ID.

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
        "headers": CORS_headers,
        "body": json.dumps(api_client.model_dump()),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
