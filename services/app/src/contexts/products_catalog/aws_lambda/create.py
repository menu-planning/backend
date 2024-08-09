import json
import uuid
from typing import Any

import anyio
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.products.add_food_product import (
    ApiAddFoodProduct,
)
from src.contexts.products_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


@lambda_exception_handler
async def async_create(event: dict[str, Any], context: Any) -> dict[str, Any]:
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("user_id")
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    current_user: SeedUser = response["body"]
    if current_user.has_permission(Permission.MANAGE_PRODUCTS):
        return {"statusCode": 403, "body": "User does not have enough privilegies."}
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
