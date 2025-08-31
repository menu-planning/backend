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
from src.logging.logger import StructlogFactory

container = Container()

# Initialize structured logger
logger = StructlogFactory.get_logger("products_catalog.fetch_product_source_name")

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
    logger.info(
        "Starting product sources query",
        operation="query_sources",
        filters_count=len(filters.__dict__) if hasattr(filters, '__dict__') else 0,
        limit=getattr(filters, 'limit', None),
        sort=getattr(filters, 'sort', None)
    )
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.sources.query(filters=filters)
    
    logger.info(
        "Product sources query completed",
        operation="query_sources",
        sources_found=len(result)
    )

    # Convert domain sources to API sources
    api_sources = []
    conversion_errors = 0
    
    logger.debug(
        "Starting domain to API conversion",
        operation="convert_sources",
        total_sources=len(result)
    )
    
    for source in result:
        try:
            api_source = ApiSource.from_domain(source)
            api_sources.append(api_source)
        except Exception as e:
            conversion_errors += 1
            # Log conversion errors but continue processing
            logger.warning(
                "Failed to convert source to API format",
                operation="convert_source",
                source_id=getattr(source, 'id', 'unknown'),
                source_type=type(source).__name__,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            continue
    
    logger.info(
        "Domain to API conversion completed",
        operation="convert_sources",
        successful_conversions=len(api_sources),
        failed_conversions=conversion_errors,
        conversion_rate=round(len(api_sources) / len(result) * 100, 2) if result else 0
    )

    # Serialize response
    response_data = {i.id: i.name for i in api_sources}
    response_body = json.dumps(response_data)
    
    logger.info(
        "Response prepared successfully",
        operation="serialize_response",
        response_items=len(response_data),
        response_size_bytes=len(response_body.encode('utf-8'))
    )

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    
    Note: Correlation ID generation is handled by the structured logging middleware.
    """
    return anyio.run(async_handler, event, context)
