from typing import Any

import anyio
from pydantic import TypeAdapter
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import ApiProduct
from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product_filter import ApiProductFilter
from src.contexts.products_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

container = Container()

ProductListTypeAdapter = TypeAdapter(list[ApiProduct])


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
        ApiProductFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at"
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Query execution with final filters
        logger.debug(f"Querying products with filters: {filters}")
        result: list[Product] = await uow.products.query(filter=filters) # type: ignore
    
    # Business context: Results summary
    logger.debug(f"Found {len(result)} products")

    # Convert domain products to API products with validation error handling
    api_products = []
    conversion_errors = 0
    
    for i, product in enumerate(result):
        try:
            api_product = ApiProduct.from_domain(product)
            api_products.append(api_product)
        except Exception as e:
            conversion_errors += 1
            logger.warning(
                f"Failed to convert product to API format - Product index: {i}, "
                f"Product ID: {getattr(product, 'id', 'unknown')}, Error: {str(e)}"
            )
            # Continue processing other products instead of failing completely
    
    if conversion_errors > 0:
        logger.warning(f"Product conversion completed with {conversion_errors} errors out of {len(result)} total products")
    
    # Serialize API products with validation error handling
    try:
        response_body = ProductListTypeAdapter.dump_json(api_products)
        logger.debug(f"Successfully serialized {len(api_products)} products")
    except Exception as e:
        logger.error(f"Failed to serialize product list to JSON: {str(e)}")
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
