"""AWS Lambda handler to create products in the catalog.

Business logic only; middleware handles auth, logging, errors, and CORS.
"""

import json
from typing import TYPE_CHECKING, Any

from src.contexts.products_catalog.core.adapters.api_schemas.commands.products.api_add_food_product import (
    ApiAddFoodProduct,
)

from .api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.products import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.core.domain.enums import Permission
from src.contexts.shared_kernel.middleware.auth.authentication import (
    products_aws_auth_middleware,
)
from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import generate_correlation_id

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="products_catalog.create_product",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    products_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="create_product_exception_handler",
        logger_name="products_catalog.create_product.errors",
    ),
    timeout=30.0,
    name="create_product_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /products for product creation.

    Request:
        Path: None
        Query: None
        Body: ApiAddFoodProduct schema with product details
        Auth: AWS Cognito JWT with MANAGE_PRODUCTS permission

    Responses:
        201: Products created successfully
        400: Invalid request body or missing required fields
        401: Unauthorized - invalid or missing JWT token
        403: Forbidden - insufficient permissions
        500: Internal server error

    Idempotency:
        No. Multiple calls with same data create duplicate products.

    Notes:
        Maps to AddFoodProductBulk command and translates errors to HTTP codes.
        Validates user permissions before processing request.
    """
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object
    if not current_user.has_permission(Permission.MANAGE_PRODUCTS):
        error_message = "User does not have enough privileges to manage products"
        raise PermissionError(error_message)

    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required and must be a non-empty string"
        raise ValueError(error_message)

    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON in request body: {e}"
        raise ValueError(error_message) from e

    api = ApiAddFoodProduct(**body)
    cmd = AddFoodProductBulk(add_product_cmds=[api.to_domain()])
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": API_headers,
        "body": json.dumps({"message": "Products created successfully"}),
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
