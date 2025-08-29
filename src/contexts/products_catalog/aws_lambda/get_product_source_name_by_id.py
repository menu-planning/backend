import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.products_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio

from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import (  # noqa: E501
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
from src.logging.logger import generate_correlation_id

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
    """
    Lambda function handler to retrieve a specific source by id.

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
    # Extract and validate source ID
    source_id = LambdaHelpers.extract_path_parameter(event, "id")
    if not source_id:
        error_message = "Source ID is required"
        raise ValueError(error_message)

    # Execute business logic
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        source = await uow.sources.get(source_id)

    # Convert domain source to API source
    validated_source = ApiSource.from_domain(source)

    # Serialize response
    response_body = json.dumps({validated_source.id: validated_source.name})

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
