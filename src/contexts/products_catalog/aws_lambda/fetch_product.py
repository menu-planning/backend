from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from pydantic import TypeAdapter
from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate import (
    ApiProduct,
    ApiProductFilter,
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
from src.logging.logger import StructlogFactory, generate_correlation_id

container = Container()

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])

# Initialize structured logger
logger = StructlogFactory.get_logger("products_catalog.fetch_product")


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="products_catalog.fetch_product",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    products_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_product_exception_handler",
        logger_name="products_catalog.fetch_product.errors",
    ),
    timeout=30.0,
    name="fetch_product_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for products.

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

    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiProductFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at",
    )

    logger.info(
        "Processing product query request",
        operation="product_query",
        filters_applied=len(filters.__dict__) if hasattr(filters, '__dict__') else 0,
        limit=getattr(filters, 'limit', 50),
        sort_by=getattr(filters, 'sort', '-updated_at')
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result: list[Product] = await uow.products.query(filters=filters)
        
    logger.info(
        "Product query completed successfully",
        operation="product_query_result",
        products_found=len(result),
        query_filters_count=len(filters.__dict__) if hasattr(filters, '__dict__') else 0
    )

    api_products = []
    conversion_errors = 0
    
    for product in result:
        try:
            api_product = ApiProduct.from_domain(product)
            api_products.append(api_product)
        except Exception as e:
            conversion_errors += 1
            product_id = getattr(product, 'id', None)
            product_name = getattr(product, 'name', None)
            
            logger.warning(
                "Product conversion to API format failed",
                product_id=product_id,
                product_name=product_name,
                error_type=e.__class__.__name__,
                error_message=str(e),
                conversion_errors_count=conversion_errors,
                operation="product_to_api_conversion"
            )
            continue

    # Log conversion summary if there were any errors
    if conversion_errors > 0:
        logger.warning(
            "Product conversion completed with errors",
            operation="product_conversion_summary",
            total_products=len(result),
            successful_conversions=len(api_products),
            conversion_errors=conversion_errors,
            success_rate=round((len(api_products) / len(result)) * 100, 2) if result else 0
        )
    
    response_body = ProductListTypeAdapter.dump_json(api_products)
    
    logger.info(
        "Product fetch request completed successfully",
        operation="fetch_product_response",
        products_returned=len(api_products),
        response_size_bytes=len(response_body),
        has_conversion_errors=conversion_errors > 0
    )

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
