"""AWS Lambda handler to fetch a product by ID.

Business logic only; middleware handles auth, logging, errors, and CORS.
"""

from typing import TYPE_CHECKING, Any

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import (
    ApiProduct,
)

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
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

from .cors_headers import CORS_headers

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="products_catalog.get_product_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    products_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="get_product_by_id_exception_handler",
        logger_name="products_catalog.get_product_by_id.errors",
    ),
    timeout=30.0,
    name="get_product_by_id_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /products/{id} for retrieving a single product.

    Request:
        Path: id (UUID v4 of the product to retrieve)
        Query: None
        Body: None
        Auth: AWS Cognito JWT token

    Responses:
        200: Product details (ApiProduct)
        400: Missing or invalid product ID
        401: Unauthorized - invalid or missing JWT token
        404: Product not found
        500: Internal server error

    Idempotency:
        Yes. Same product ID returns identical results.

    Notes:
        Maps to UnitOfWork.products.get() and translates errors to HTTP codes.
        Returns 404 if product does not exist.
    """
    product_id = LambdaHelpers.extract_path_parameter(event, "id")
    if not product_id:
        error_message = "Product ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        product = await uow.products.get(product_id)

    validated_product = ApiProduct.from_domain(product)
    response_body = validated_product.model_dump_json()

    return {
        "statusCode": 200,
        "headers": CORS_headers,
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
