"""
Webhook Health Check Lambda Endpoint

Health check Lambda for webhook processor monitoring.
Verifies that the webhook processing infrastructure is operational.
"""

from typing import Any, Dict
import json
from datetime import UTC, datetime

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler
)
from src.logging.logger import logger

from .CORS_headers import CORS_headers

# Initialize container
container = Container()


@lambda_exception_handler(CORS_headers)
async def async_lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Health check endpoint for webhook processor monitoring.
    
    Verifies that the webhook processing infrastructure is operational.
    
    Args:
        event: Lambda event
        context: Lambda context object
        
    Returns:
        Dict containing statusCode, headers, and body for Lambda response
    """
    try:
        logger.info("Webhook processor health check requested")
        
        # Basic health check - verify container can bootstrap
        try:
            container.bootstrap()
            logger.debug("Container bootstrap successful")
        except Exception as e:
            logger.error(f"Container bootstrap failed: {e}")
            return {
                "statusCode": 503,
                "headers": CORS_headers,
                "body": json.dumps({
                    "status": "unhealthy",
                    "error": "Container bootstrap failed",
                    "timestamp": datetime.now(UTC).isoformat() + "Z"
                }),
            }
        
        # Return healthy status
        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": json.dumps({
                "status": "healthy",
                "service": "webhook_processor",
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "version": "1.0.0"
            }),
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({
                "status": "error",
                "error": "Health check failed",
                "timestamp": datetime.now(UTC).isoformat() + "Z"
            }),
        }


# Synchronous handler for Lambda runtime compatibility
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Synchronous wrapper for async webhook health handler."""
    import anyio
    return anyio.run(async_lambda_handler, event, context) 