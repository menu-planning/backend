"""
Single Response Query Lambda Handler

Lambda function for querying stored responses for form creators with proper authorization.
Handles single query operations with pagination and filtering.
"""

from typing import Any, Dict
import anyio
from pydantic import ValidationError

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.api_schemas.commands.response_query_commands import (
    ResponseQueryRequest
)
from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_api_logging_middleware
)
from src.contexts.client_onboarding.core.adapters.validators.ownership_validator import (
    FormOwnershipValidator
)
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler
)
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id
from src.contexts.client_onboarding.aws_lambda.shared.query_executor import execute_query

from .CORS_headers import CORS_headers

container = Container()
logging_middleware = create_api_logging_middleware()


@lambda_exception_handler(CORS_headers)
async def async_lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler to query form responses.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        correlation_id = generate_correlation_id()
        operation_context["correlation_id"] = correlation_id
        
        try:
            # Extract and validate request
            body = LambdaHelpers.extract_request_body(event, parse_json=True)
            query_request = ResponseQueryRequest.model_validate(body)
            
            # Execute query
            async with container.get_uow() as uow:
                ownership_validator = FormOwnershipValidator()
                result = await execute_query(query_request, uow, ownership_validator)
                await uow.commit()
            
            # Return response
            response_body = result.model_dump_json()
            return {
                "statusCode": 200,
                "headers": CORS_headers,
                "body": response_body,
            }
            
        except ValidationError as e:
            logger.error(f"Query validation error: {e}")
            return LambdaHelpers.format_error_response(
                message="Invalid query request",
                status_code=400,
                error_code="VALIDATION_ERROR",
                cors_headers=CORS_headers
            )
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return LambdaHelpers.format_error_response(
                message="Query processing failed",
                status_code=500,
                error_code="QUERY_ERROR",
                cors_headers=CORS_headers
            )


# Synchronous wrapper for Lambda runtime
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Synchronous wrapper for query responses handler."""
    return anyio.run(async_lambda_handler, event, context) 