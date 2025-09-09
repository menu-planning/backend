"""AWS Lambda handler to fetch products by filters.

Business logic only; middleware handles auth, logging, errors, and CORS.
"""

from typing import TYPE_CHECKING, Any

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import (
    ApiProductFilter,
)

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from pydantic import TypeAdapter
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.middleware.auth.authentication import (
    products_aws_auth_middleware,
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
from src.logging.logger import StructlogFactory, generate_correlation_id

from .api_headers import API_headers

container = Container()

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])

# Structured logger for this handler
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
    """Handle GET /products for querying products with filters.

    Request:
        Path: None
        Query: ApiProductFilter parameters (limit, sort, filters, pagination)
        Body: None
        Auth: AWS Cognito JWT token

    Responses:
        200: List of products matching filters (ApiProduct[])
        400: Invalid query parameters
        401: Unauthorized - invalid or missing JWT token
        500: Internal server error

    Idempotency:
        Yes. Same query parameters return identical results.

    Notes:
        Maps to UnitOfWork.products.query() and translates errors to HTTP codes.
        Supports pagination, sorting, and filtering. Default limit: 50, sort: -updated_at.
        Logs conversion errors but continues processing remaining products.
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
        filters_applied=len(filters.__dict__) if hasattr(filters, "__dict__") else 0,
        limit=getattr(filters, "limit", 50),
        sort_by=getattr(filters, "sort", "-updated_at"),
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result: list[Product] = await uow.products.query(filters=filters)

    logger.info(
        "Product query completed successfully",
        operation="product_query_result",
        products_found=len(result),
        query_filters_count=(
            len(filters.__dict__) if hasattr(filters, "__dict__") else 0
        ),
    )

    api_products = []
    conversion_errors = 0

    for product in result:
        try:
            api_product = ApiProduct.from_domain(product)
            api_products.append(api_product)
        except Exception as e:
            conversion_errors += 1
            product_id = getattr(product, "id", None)
            product_name = getattr(product, "name", None)

            logger.warning(
                "Product conversion to API format failed",
                product_id=product_id,
                product_name=product_name,
                error_type=e.__class__.__name__,
                error_message=str(e),
                conversion_errors_count=conversion_errors,
                operation="product_to_api_conversion",
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
            success_rate=(
                round((len(api_products) / len(result)) * 100, 2) if result else 0
            ),
        )

    response_body = ProductListTypeAdapter.dump_json(api_products)

    logger.info(
        "Product fetch request completed successfully",
        operation="fetch_product_response",
        products_returned=len(api_products),
        response_size_bytes=len(response_body),
        has_conversion_errors=conversion_errors > 0,
    )

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Sync entrypoint wrapper for the async handler.

    Args:
        event: AWS Lambda event dict containing request data.
        context: AWS Lambda context object.

    Returns:
        dict[str, Any]: HTTP response with status code, headers, and body.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
