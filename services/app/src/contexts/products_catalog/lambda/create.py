import json
import uuid
from typing import Any

import anyio
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.products.add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.seedwork.shared.endpoints.decorators import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


@lambda_exception_handler
async def async_create(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # Extract the product ID from the path parameters
    body = event.get("body", "")
    api = ApiAddFoodProduct(**body)
    cmd = AddFoodProductBulk(add_product_cmds=[api.to_domain()])
    bus: MessageBus = Container().bootstrap()
    products_ids = await bus.handle(cmd)
    return {
        "statusCode": 201,
        "body": json.dumps(
            {"message": "Products created successfully", "products_ids": products_ids}
        ),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create products.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_create, event, context)
