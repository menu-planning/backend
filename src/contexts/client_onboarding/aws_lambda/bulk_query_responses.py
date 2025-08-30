"""
Bulk Response Query Lambda Handler

Lambda function for executing multiple response queries in a single request.
Handles bulk query operations with error tracking and partial success support.
"""

from typing import Any

import anyio

from src.contexts.client_onboarding.aws_lambda.shared import (
    CORS_headers,
    execute_query,
)
from src.contexts.client_onboarding.core import Container
from src.contexts.client_onboarding.core.adapters import (
    BulkResponseQueryRequest,
    BulkResponseQueryResponse,
    FormOwnershipValidator,
    ResponseQueryResponse,
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
        logger_name="client_onboarding.bulk_query_responses",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    aws_lambda_exception_handler_middleware(
        name="bulk_query_responses_exception_handler",
        logger_name="client_onboarding.bulk_query_responses.errors",
    ),
    timeout=30.0,
    name="bulk_query_responses_handler",
)
async def async_lambda_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """
    Lambda function handler to execute multiple queries in a single request.

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

    bulk_request = BulkResponseQueryRequest.model_validate_json(body)

    # Execute queries
    results = []
    errors = []
    successful_queries = 0

    async with container.get_uow() as uow:
        ownership_validator = FormOwnershipValidator()

        for query in bulk_request.queries:
            try:
                result = await execute_query(query, uow, ownership_validator)
                results.append(result)
                if result.success:
                    successful_queries += 1
            except Exception as e:
                results.append(
                    ResponseQueryResponse(
                        success=False,
                        query_type=query.query_type,
                        total_count=0,
                        returned_count=0,
                        forms=None,
                        responses=None,
                        pagination=None,
                    )
                )
                errors.append(f"Query {len(results)} failed: {e!s}")

        await uow.commit()

    # Create bulk response
    bulk_response = BulkResponseQueryResponse(
        success=successful_queries == len(bulk_request.queries),
        total_queries=len(bulk_request.queries),
        successful_queries=successful_queries,
        results=results,
        errors=errors if errors else None,
    )

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": bulk_response.model_dump_json(),
    }


# Synchronous wrapper for Lambda runtime
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for bulk query responses handler."""
    generate_correlation_id()
    return anyio.run(async_lambda_handler, event, context)
