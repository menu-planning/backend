"""AWS Lambda handler for retrieving a tag by id."""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import app_settings
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)
from src.contexts.shared_kernel.middleware.auth.authentication import (
    recipes_aws_auth_middleware,
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

from ..api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.get_tag_by_id",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=app_settings.enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="get_tag_by_id_exception_handler",
        logger_name="recipes_catalog.get_tag_by_id.errors",
    ),
    timeout=30.0,
    name="get_tag_by_id_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /tags/{tag_id} for tag retrieval.

    Request:
        Path: tag_id (UUID v4) - tag identifier
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: Tag found and returned as JSON
        400: Missing or invalid tag ID
        404: Tag not found
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls return same result.

    Notes:
        Maps to Tag repository get() method and translates errors to HTTP codes.
        No special permissions required for read access.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    # Extract tag ID from path parameters
    tag_id = LambdaHelpers.extract_path_parameter(event, "tag_id")
    if not tag_id:
        error_message = "Tag ID is required"
        raise ValueError(error_message)

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Get tag by ID
        tag = await uow.tags.get(tag_id)

    if not tag:
        error_message = "Tag not found"
        raise ValueError(error_message)

    # Convert domain tag to API tag
    api_tag = ApiTag.from_domain(tag)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": json.dumps(api_tag.model_dump()),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for tag retrieval.

    Args:
        event: AWS Lambda event with HTTP request details
        context: AWS Lambda execution context

    Returns:
        HTTP response with status code, headers, and body

    Notes:
        Generates correlation ID and delegates to async handler.
        Wraps async execution in anyio runtime.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
