import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from pydantic import TypeAdapter

from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_filter import (
    ApiClassificationFilter,
)
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import (
    ApiSource,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.contexts.shared_kernel.middleware.auth.authentication import (
    products_aws_auth_middleware,
)
from src.contexts.shared_kernel.middleware.decorators import async_endpoint_handler
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import generate_correlation_id, logger

container = Container()

SourceListTypeAdapter = TypeAdapter(list[ApiSource])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="products_catalog.fetch_product_source_name",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    products_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_product_source_name_exception_handler",
        logger_name="products_catalog.fetch_product_source_name.errors",
    ),
    timeout=30.0,
    name="fetch_product_source_name_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for product sources.

    This handler focuses purely on business logic. All cross-cutting concerns
    are handled by the unified middleware:
    - Authentication: AuthenticationMiddleware provides event["_auth_context"]
    - Logging: StructuredLoggingMiddleware handles request/response logging
    - Error Handling: ExceptionHandlerMiddleware catches and formats all errors
    - CORS: Handled automatically by the middleware system

    Args:
        event: AWS Lambda event dictionary with _auth_context added by middleware
        context: AWS Lambda context object
    """
    # Authentication is handled by middleware - user is validated
    # Process query filters
    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiClassificationFilter,
        use_multi_value=False,
        default_limit=100,
        default_sort="-created_at",
    )

    # Execute business logic
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.sources.query(filters=filters)

    # Convert domain sources to API sources
    api_sources = []
    for source in result:
        try:
            api_source = ApiSource.from_domain(source)
            api_sources.append(api_source)
        except Exception as e:
            # Log conversion errors but continue processing
            logger.warning(
                f"Failed to convert source to API format - "
                f"Source ID: {getattr(source, 'id', 'unknown')}, Error: {e!s}"
            )
            continue

    # Serialize response
    response_body = json.dumps({i.id: i.name for i in api_sources})

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
