"""
Webhook Processing Lambda Endpoint

Main webhook processing Lambda with proper error handling and validation.
Handles TypeForm webhook payloads with security verification, payload processing,
and data storage using the existing webhook processing infrastructure.
"""

from typing import Any, Dict
import json
from datetime import UTC, datetime

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.adapters.api_schemas.commands import ApiProcessWebhook
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_webhook_logging_middleware
)
from src.contexts.client_onboarding.core.adapters.middleware.error_middleware import (
    ClientOnboardingErrorMiddleware
)
from src.contexts.client_onboarding.core.services.exceptions import (
    WebhookPayloadError,
    FormResponseProcessingError,
    OnboardingFormNotFoundError,
)
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler
)
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id
from pydantic import ValidationError

from .CORS_headers import CORS_headers

# Initialize container and middleware
container = Container()
logging_middleware = create_webhook_logging_middleware()
error_middleware = ClientOnboardingErrorMiddleware(
    logger_name="webhook_processor",
    include_stack_trace=False,  # Don't expose stack traces in production
    expose_internal_details=False,  # Security: don't expose internal details
    default_error_message="Webhook processing failed"
)


@lambda_exception_handler(CORS_headers)
async def async_lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler to process TypeForm webhook payloads.
    
    This handler:
    1. Validates webhook signature for security
    2. Processes the TypeForm response data
    3. Extracts client identifiers
    4. Stores the processed data in the database
    5. Returns appropriate status responses
    
    Args:
        event: Lambda event containing webhook payload and headers
        context: Lambda context object
        
    Returns:
        Dict containing statusCode, headers, and body for Lambda response
    """
    async with logging_middleware.log_request_response(event, context):
        correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"Webhook processing started. Correlation ID: {correlation_id}")
            logger.debug(f"Webhook event received. {LambdaHelpers.extract_log_data(event, include_body=False)}")  # Don't log full body for security
            
            # Extract webhook payload and headers (validation and normalization handled by ApiProcessWebhook)
            raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
            if isinstance(raw_body, dict):
                raw_body = json.dumps(raw_body)
            elif not isinstance(raw_body, str):
                raw_body = str(raw_body)
            headers = event.get("headers", {}) or {}
            
            # Process webhook by dispatching a command through the MessageBus
            try:
                bus = container.bootstrap()
                logger.debug("Starting webhook payload processing via MessageBus")

                # Build API schema then convert to domain command for consistency with other endpoints
                api_cmd = ApiProcessWebhook(payload=raw_body, headers=headers)
                cmd = api_cmd.to_domain()
                await bus.handle(cmd)

                logger.info("Webhook processed successfully")

                response_body = {
                    "message": "Webhook processed successfully",
                    "processed_at": datetime.now(UTC).isoformat() + "Z",
                }

                return {
                    "statusCode": 200,
                    "headers": CORS_headers,
                    "body": json.dumps(response_body),
                }
                    
            except ValidationError as ve:
                logger.warning(f"Invalid webhook payload: {ve}")
                return {
                    "statusCode": 400,
                    "headers": CORS_headers,
                    "body": json.dumps({
                        "message": "Invalid webhook request",
                        "correlation_id": correlation_id,
                    }),
                }
            except Exception as e:
                logger.error(f"Webhook processing error: {e}", exc_info=True)
                
                # Use error middleware to handle and categorize the exception
                async with error_middleware.error_context("webhook_processing") as _:
                    # Log and categorize error, but handle response manually
                    pass
                
                # Map known domain exceptions to appropriate statuses
                status_code = 500
                if isinstance(e, WebhookPayloadError):
                    status_code = 400
                elif isinstance(e, OnboardingFormNotFoundError):
                    status_code = 404
                elif isinstance(e, FormResponseProcessingError):
                    status_code = 422

                return {
                    "statusCode": status_code,
                    "headers": CORS_headers,
                    "body": json.dumps({
                        "message": "Webhook processing failed" if status_code != 200 else "OK",
                        "correlation_id": correlation_id,
                    }),
                }
                    
        except Exception as e:
            logger.error(f"Critical webhook handler error: {e}", exc_info=True)
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": json.dumps({
                    "message": "Critical webhook processing error",
                    "correlation_id": correlation_id
                }),
            }


# Synchronous handler for Lambda runtime compatibility
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Synchronous wrapper for async webhook processor handler."""
    import anyio
    return anyio.run(async_lambda_handler, event, context) 