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
from src.contexts.client_onboarding.services.webhook_processor import process_typeform_webhook
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_webhook_logging_middleware
)
from src.contexts.client_onboarding.core.adapters.middleware.error_middleware import (
    ClientOnboardingErrorMiddleware
)
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler
)
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

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
            
            # Extract webhook payload and headers
            try:
                raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
                
                # Ensure we have a string payload for webhook processing
                if isinstance(raw_body, dict):
                    raw_body = json.dumps(raw_body)
                elif not isinstance(raw_body, str):
                    raw_body = str(raw_body)
                
                if not raw_body:
                    logger.warning("Empty webhook payload received")
                    return {
                        "statusCode": 400,
                        "headers": CORS_headers,
                        "body": json.dumps({"message": "Empty payload"}),
                    }
                
                # Extract headers for signature verification
                headers = event.get("headers", {}) or {}
                
                # Handle case-insensitive headers (API Gateway vs ALB differences)
                normalized_headers = {}
                for key, value in headers.items():
                    normalized_headers[key.lower()] = value
                
                logger.debug(f"Processing webhook with {len(raw_body)} bytes payload and {len(normalized_headers)} headers")
                
            except Exception as e:
                logger.error(f"Failed to extract webhook payload: {e}")
                return {
                    "statusCode": 400,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Invalid webhook format"}),
                }
            
            # Process webhook using existing infrastructure
            try:
                # Use container to get UoW factory
                bus = container.bootstrap()
                
                def uow_factory():
                    return bus.uow
                
                logger.debug("Starting webhook payload processing")
                
                # Process the webhook
                success, error_message, response_id = await process_typeform_webhook(
                    payload=raw_body,
                    headers=normalized_headers,
                    uow_factory=uow_factory
                )
                
                if success:
                    logger.info(f"Webhook processed successfully. Response ID: {response_id}")
                    
                    response_body = {
                        "message": "Webhook processed successfully",
                        "response_id": response_id,
                        "processed_at": datetime.now(UTC).isoformat() + "Z"
                    }
                    
                    return {
                        "statusCode": 200,
                        "headers": CORS_headers,
                        "body": json.dumps(response_body),
                    }
                else:
                    logger.warning(f"Webhook processing failed: {error_message}")
                    
                    # Determine appropriate error code based on error message
                    if "signature" in (error_message or "").lower():
                        status_code = 401  # Unauthorized for signature failures
                    elif "not found" in (error_message or "").lower():
                        status_code = 404  # Not found for missing forms
                    elif "validation" in (error_message or "").lower():
                        status_code = 400  # Bad request for validation errors
                    elif "rate limit" in (error_message or "").lower():
                        status_code = 429  # Too many requests for rate limits
                    else:
                        status_code = 422  # Unprocessable entity for other processing errors
                    
                    return {
                        "statusCode": status_code,
                        "headers": CORS_headers,
                        "body": json.dumps({
                            "message": "Webhook processing failed",
                            "error": error_message,
                            "correlation_id": correlation_id
                        }),
                    }
                    
            except Exception as e:
                logger.error(f"Webhook processing error: {e}", exc_info=True)
                
                # Use error middleware to handle and categorize the exception
                async with error_middleware.error_context("webhook_processing") as _:
                    # Log and categorize error, but handle response manually
                    pass
                
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({
                        "message": "Internal webhook processing error",
                        "correlation_id": correlation_id
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