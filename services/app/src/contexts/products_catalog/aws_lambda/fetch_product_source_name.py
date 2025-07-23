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
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event)}")
    
    if not LambdaHelpers.is_localstack_environment():
        user_id = LambdaHelpers.extract_user_id(event)        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": CORS_headers,
                "body": '{"message": "User ID not found in request context"}',
            }
        
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            response["headers"] = CORS_headers
            return response
    
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
        result = await uow.sources.query(filter=filters)
    validated_sources = [ApiSource.from_domain(i) for i in result] if result else []
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({i.id:i.name for i in validated_sources}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
