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
from src.logging.logger import generate_correlation_id, logger

container = Container()

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])


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

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result: list[Product] = await uow.products.query(filters=filters)

    api_products = []
    for product in result:
        try:
            api_product = ApiProduct.from_domain(product)
            api_products.append(api_product)
        except Exception as e:
            logger.warning(
                f"Failed to convert product to API format - "
                f"Product ID: {getattr(product, 'id', 'unknown')}, Error: {e!s}"
            )
            continue

    response_body = ProductListTypeAdapter.dump_json(api_products)

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
