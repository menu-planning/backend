import urllib.parse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from pydantic import TypeAdapter

from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate import (
    ApiProduct,
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
from src.logging.logger import generate_correlation_id

container = Container()

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="products_catalog.search_product_similar_name",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    products_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="search_product_similar_name_exception_handler",
        logger_name="products_catalog.search_product_similar_name.errors",
    ),
    timeout=30.0,
    name="search_product_similar_name_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to search products by name similarity.

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
    # Extract and validate name parameter
    name = LambdaHelpers.extract_path_parameter(event, "name")
    if not name:
        error_message = "Name parameter is required"
        raise ValueError(error_message)

    # URL decode the name parameter
    name = urllib.parse.unquote(name)

    # Execute business logic
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.products.list_top_similar_names(name)

    # Convert domain products to API products
    api_products = [ApiProduct.from_domain(i) for i in result] if result else []

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ProductListTypeAdapter.dump_json(api_products),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
