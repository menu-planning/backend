import json
from typing import Any

import anyio
from pydantic import TypeAdapter
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_filter import ApiClassificationFilter
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

SourceListTypeAdapter = TypeAdapter(list[ApiSource])

@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for products.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication using the new utility
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=False
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, user_id = auth_result  # Extract user_id (though we don't need it for this endpoint)
    
    filters = LambdaHelpers.process_query_filters(
        event,
        ApiClassificationFilter,
        use_multi_value=False,
        default_limit=100,
        default_sort="-created_at"
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Query execution with final filters
        logger.debug(f"Querying sources with filters: {filters}")
        result = await uow.sources.query(filter=filters)
    
    # Business context: Results summary
    logger.debug(f"Found {len(result)} sources")
    
    # Convert domain sources to API sources with validation error handling
    api_sources = []
    conversion_errors = 0
    
    for i, source in enumerate(result):
        try:
            api_source = ApiSource.from_domain(source)
            api_sources.append(api_source)
        except Exception as e:
            conversion_errors += 1
            logger.warning(
                f"Failed to convert source to API format - Source index: {i}, "
                f"Source ID: {getattr(source, 'id', 'unknown')}, Error: {str(e)}"
            )
            # Continue processing other sources instead of failing completely
    
    if conversion_errors > 0:
        logger.warning(f"Source conversion completed with {conversion_errors} errors out of {len(result)} total sources")
    
    # Serialize API sources with validation error handling
    try:
        response_body = json.dumps({i.id: i.name for i in api_sources})
        logger.debug(f"Successfully serialized {len(api_sources)} sources")
    except Exception as e:
        logger.error(f"Failed to serialize source list to JSON: {str(e)}")
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
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
