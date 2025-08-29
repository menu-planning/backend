import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio

from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.products_catalog.core.adapters.api_schemas.commands.products import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.products import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.core.domain.enums import Permission
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
    """
    Lambda function handler to create products.

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
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Check user permissions
    if not current_user.has_permission(Permission.MANAGE_PRODUCTS):
        error_message = "User does not have enough privileges to manage products"
        raise PermissionError(error_message)

    # Parse and validate request body
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required and must be a non-empty string"
        raise ValueError(error_message)

    # Parse JSON body
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError as e:
        error_message = f"Invalid JSON in request body: {e}"
        raise ValueError(error_message) from e

    # Validate API schema
    api = ApiAddFoodProduct(**body)
    cmd = AddFoodProductBulk(add_product_cmds=[api.to_domain()])

    # Execute business logic
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Products created successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
