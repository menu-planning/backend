import json
import os
import uuid
from typing import Any

import anyio
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.update import (
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

container = Container()


@lambda_exception_handler
async def async_update(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    recipe_id = event.get("pathParameters", {}).get("id")
    async with bus.uow as uow:
        try:
            recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundException:
            return {
                "statusCode": 403,
                "body": json.dumps({"message": f"Recipe {recipe_id} not in database."}),
            }
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    body = event.get("body", "")
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response

    api = ApiUpdateRecipe(recipe_id=recipe_id, updates=body)
    cmd = api.to_domain()
    await bus.handle(cmd)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Recipe updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a recipe by its id.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_update, event, context)
