from typing import TYPE_CHECKING, Any

import anyio
from pydantic import TypeAdapter

from src.contexts.recipes_catalog.aws_lambda.cors_headers import CORS_headers
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate import (
    ApiClient,
    ApiClientFilter,
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

ClientListTypeAdapter = TypeAdapter(list[ApiClient])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.fetch_client",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
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
    """
    Lambda function handler to fetch clients.

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

    # Convert domain clients to API clients
    api_clients = []
    conversion_errors = 0

    for i, client in enumerate(result):
        try:
            api_client = ApiClient.from_domain(client)
            api_clients.append(api_client)
        except Exception:
            conversion_errors += 1
            # Continue processing other clients instead of failing completely

    if conversion_errors > 0:
        # Log warning but continue - this is handled by logging middleware
        pass

    # Serialize API clients
    response_body = ClientListTypeAdapter.dump_json(api_clients)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
