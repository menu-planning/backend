"""AWS Lambda handler to fetch a product source by ID.

Business logic only; middleware handles auth, logging, errors, and CORS.
"""

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import (
    ApiSource,
)
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
        logger_name="products_catalog.get_product_source_name_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    products_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="get_product_source_name_by_id_exception_handler",
        logger_name="products_catalog.get_product_source_name_by_id.errors",
    ),
    timeout=30.0,
    name="get_product_source_name_by_id_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /product-sources/{id} for retrieving a single product source.

    Request:
        Path: id (UUID v4 of the product source to retrieve)
        Query: None
        Body: None
        Auth: AWS Cognito JWT token

    Responses:
        200: Source details as {id: name} mapping (dict[str, str])
        400: Missing or invalid source ID
        401: Unauthorized - invalid or missing JWT token
        404: Source not found
        500: Internal server error

    Idempotency:
        Yes. Same source ID returns identical results.

    Notes:
        Maps to UnitOfWork.sources.get() and translates errors to HTTP codes.
        Returns 404 if source does not exist.
        Returns simplified {id: name} mapping instead of full ApiSource object.
    """
    source_id = LambdaHelpers.extract_path_parameter(event, "id")
    if not source_id:
        error_message = "Source ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        source = await uow.sources.get(source_id)

    validated_source = ApiSource.from_domain(source)
    response_body = json.dumps({validated_source.id: validated_source.name})

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
