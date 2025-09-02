"""AWS Lambda handler to search products by name similarity.

Business logic only; middleware handles auth, logging, errors, and CORS.
"""

import urllib.parse
from typing import TYPE_CHECKING, Any

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from pydantic import TypeAdapter
from src.contexts.products_catalog.aws_lambda.cors_headers import CORS_headers
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
    """Handle GET /products/search/{name} for product name similarity search.

    Request:
        Path: name (URL-encoded product name to search for)
        Query: None
        Body: None
        Auth: AWS Cognito JWT token

    Responses:
        200: List of products with similar names (ApiProduct[])
        400: Missing or invalid name parameter
        401: Unauthorized - invalid or missing JWT token
        500: Internal server error

    Idempotency:
        Yes. Same name parameter returns identical results.

    Notes:
        Maps to UnitOfWork.products.list_top_similar_names() and translates errors to HTTP codes.
        Name parameter is URL-decoded before processing.
    """
    name = LambdaHelpers.extract_path_parameter(event, "name")
    if not name:
        error_message = "Name parameter is required"
        raise ValueError(error_message)

    name = urllib.parse.unquote(name)
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.products.list_top_similar_names(name)

    api_products = [ApiProduct.from_domain(i) for i in result] if result else []

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": ProductListTypeAdapter.dump_json(api_products),
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
