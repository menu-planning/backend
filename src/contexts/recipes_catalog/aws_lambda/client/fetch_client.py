"""AWS Lambda handler for querying clients."""

from typing import TYPE_CHECKING, Any

import anyio
from pydantic import TypeAdapter
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import (
    ApiClient,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_filter import (
    ApiClientFilter,
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

ClientListTypeAdapter = TypeAdapter(list[ApiClient])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.fetch_client",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_client_exception_handler",
        logger_name="recipes_catalog.fetch_client.errors",
    ),
    timeout=30.0,
    name="fetch_client_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /clients for client querying with filters.

    Request:
        Query: filters (optional) - ApiClientFilter schema with pagination, sorting, and search criteria
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: List of clients matching criteria returned as JSON
        400: Invalid filter parameters
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same filters return same result.

    Notes:
        Maps to Client repository query() method and translates errors to HTTP codes.
        Default limit: 50, default sort: -updated_at (newest first).
        User-specific tag filtering applied automatically.
        Continues processing on individual client conversion errors.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiClientFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at",
    )

    # Handle user-specific tag filtering
    if current_user and filters.get("tags"):
        filters["tags"] = [(i, current_user.id) for i in filters["tags"]]
    if current_user and filters.get("tags_not_exists"):
        filters["tags_not_exists"] = [
            (i, current_user.id) for i in filters["tags_not_exists"]
        ]

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.clients.query(filters=filters)

    api_clients = [ApiClient.from_domain(client) for client in result]

    response_body = ClientListTypeAdapter.dump_json(api_clients)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for client querying.

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
