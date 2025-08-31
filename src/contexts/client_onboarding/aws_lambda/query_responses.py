"""
Single Response Query Lambda Handler

Lambda function for querying stored responses for form creators
with proper authorization.
Handles single query operations with pagination and filtering.
"""

from typing import Any

import anyio
from src.contexts.client_onboarding.aws_lambda.shared import (
    CORS_headers,
    execute_query,
)
from src.contexts.client_onboarding.core.adapters import (
    FormOwnershipValidator,
)
from src.contexts.client_onboarding.core.adapters.api_schemas.queries import (
    ResponseQueryRequest,
)
from src.contexts.client_onboarding.core.bootstrap.container import Container
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
        logger_name="client_onboarding.query_responses",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    aws_lambda_exception_handler_middleware(
        name="query_responses_exception_handler",
        logger_name="client_onboarding.query_responses.errors",
    ),
    timeout=30.0,
    name="query_responses_handler",
)
async def async_lambda_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to query form responses.

    This handler focuses purely on business logic. All cross-cutting concerns
    are handled by the unified middleware:
    - Logging: StructuredLoggingMiddleware handles request/response logging
    - Error Handling: ExceptionHandlerMiddleware catches and formats all errors
    - CORS: Handled automatically by the middleware system
    """
    # Extract and validate request
    body = event.get("body", "")
    if not isinstance(body, str) or not body.strip():
        error_message = "Request body is required and must be a non-empty string"
        raise ValueError(error_message)

    query_request = ResponseQueryRequest.model_validate_json(body)

    # Execute query
    async with container.get_uow() as uow:
        ownership_validator = FormOwnershipValidator()
        result = await execute_query(query_request, uow, ownership_validator)
        await uow.commit()

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": result.model_dump_json(),
    }


# Synchronous wrapper for Lambda runtime
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for query responses handler."""
    generate_correlation_id()
    return anyio.run(async_lambda_handler, event, context)
