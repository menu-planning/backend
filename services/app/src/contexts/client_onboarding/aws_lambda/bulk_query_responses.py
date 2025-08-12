"""
Bulk Response Query Lambda Handler

Lambda function for executing multiple response queries in a single request.
Handles bulk query operations with error tracking and partial success support.
"""

from typing import Any, Dict
import anyio
from pydantic import ValidationError

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.adapters.api_schemas.queries.response_queries import (
    BulkResponseQueryRequest, BulkResponseQueryResponse, ResponseQueryResponse
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
    Lambda function handler to execute multiple queries in a single request.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        correlation_id = generate_correlation_id()
        operation_context["correlation_id"] = correlation_id
        
        try:
            # Extract and validate request
            body = LambdaHelpers.extract_request_body(event, parse_json=True)
            bulk_request = BulkResponseQueryRequest.model_validate(body)
            
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
                        logger.error(f"Error in bulk query: {e}")
                        results.append(ResponseQueryResponse(
                            success=False,
                            query_type=query.query_type,
                            total_count=0,
                            returned_count=0,
                            forms=None,
                            responses=None,
                            pagination=None
                        ))
                        errors.append(f"Query {len(results)} failed: {str(e)}")
                
                await uow.commit()
            
            # Create bulk response
            bulk_response = BulkResponseQueryResponse(
                success=successful_queries == len(bulk_request.queries),
                total_queries=len(bulk_request.queries),
                successful_queries=successful_queries,
                results=results,
                errors=errors if errors else None
            )
            
            # Return response
            response_body = bulk_response.model_dump_json()
            return {
                "statusCode": 200,
                "headers": CORS_headers,
                "body": response_body,
            }
            
        except ValidationError as e:
            logger.error(f"Bulk query validation error: {e}")
            return LambdaHelpers.format_error_response(
                message="Invalid bulk query request",
                status_code=400,
                error_code="VALIDATION_ERROR",
                cors_headers=CORS_headers
            )
        except Exception as e:
            logger.error(f"Bulk query processing error: {e}")
            return LambdaHelpers.format_error_response(
                message="Bulk query processing failed",
                status_code=500,
                error_code="BULK_QUERY_ERROR",
                cors_headers=CORS_headers
            )


# Synchronous wrapper for Lambda runtime
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Synchronous wrapper for bulk query responses handler."""
    return anyio.run(async_lambda_handler, event, context) 