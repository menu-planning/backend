import json
from typing import Any

import anyio
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import ApiSource
from src.contexts.products_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific source by id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication using the new utility
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=False
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, user_id = auth_result  # Extract user_id (though we don't need it for this endpoint)
    
    source_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    if not source_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": '{"message": "Source ID is required"}',
        }
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Source retrieval by ID
        logger.debug(f"Retrieving source with ID: {source_id}")
        try:
            source = await uow.sources.get(source_id)
        except Exception as e:
            logger.error(f"Source not found: {source_id} - {e}")
            raise e
    
    # Business context: Source found and validated
    logger.debug(f"Source found: {source_id}")
    
    # Convert domain source to API source with validation error handling
    try:
        validated_source = ApiSource.from_domain(source)
        logger.debug(f"Successfully converted source {source_id} to API format")
    except Exception as e:
        logger.error(f"Failed to convert source {source_id} to API format: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during source conversion"}',
        }
    
    # Serialize API source with validation error handling
    try:
        response_body = json.dumps({validated_source.id: validated_source.name})
        logger.debug(f"Successfully serialized source {source_id}")
    except Exception as e:
        logger.error(f"Failed to serialize source {source_id} to JSON: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during response serialization"}',
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to retrieve a specific product by id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
