"""Webhook processing Lambda handler for client onboarding.

Main webhook processing Lambda with proper error handling and validation.
Handles TypeForm webhook payloads with security verification, payload processing,
and data storage using the existing webhook processing infrastructure.
"""

import json
from datetime import UTC, datetime
from typing import Any

import anyio
from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.api_process_webhook import (
    ApiProcessWebhook,
)
from src.contexts.client_onboarding.core.bootstrap.container import Container
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
        logger_name="client_onboarding.webhook_processor",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    aws_lambda_exception_handler_middleware(
        name="webhook_processor_exception_handler",
        logger_name="client_onboarding.webhook_processor.errors",
    ),
    timeout=30.0,
    name="webhook_processor_handler",
)
async def async_lambda_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /webhook for processing TypeForm webhook payloads.

    Request:
        Path: N/A
        Query: N/A
        Body: TypeForm webhook payload (JSON)
        Auth: None (webhook endpoint)

    Responses:
        200: Webhook processed successfully
        400: Invalid webhook payload or signature
        500: Internal server error

    Idempotency:
        No. Each webhook call processes fresh data.

    Notes:
        Maps to ProcessWebhook command via MessageBus.
        Validates webhook signature, processes TypeForm response data,
        extracts client identifiers, and stores processed data.
        Cross-cutting concerns handled by middleware: logging, error handling, CORS.
    """
    # Extract webhook payload and headers
    # (validation and normalization handled by ApiProcessWebhook)
    raw_body = event.get("body", "")
    if isinstance(raw_body, dict):
        raw_body = json.dumps(raw_body)
    elif not isinstance(raw_body, str):
        raw_body = str(raw_body)
    headers = event.get("headers", {}) or {}

    # Process webhook by dispatching a command through the MessageBus
    bus = container.bootstrap()

    # Build API schema then convert to domain command for consistency with other
    # endpoints
    api_cmd = ApiProcessWebhook(payload=raw_body, headers=headers)
    cmd = api_cmd.to_domain()
    await bus.handle(cmd)

    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Webhook processed successfully",
            "details": {"processed_at": datetime.now(UTC).isoformat() + "Z"},
        }),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for webhook processor handler.

    Args:
        event: AWS Lambda event dictionary
        context: AWS Lambda context object

    Returns:
        Dict containing statusCode, headers, and body for Lambda response
    """
    generate_correlation_id()
    return anyio.run(async_lambda_handler, event, context)
