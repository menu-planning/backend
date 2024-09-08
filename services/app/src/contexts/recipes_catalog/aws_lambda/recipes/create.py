import json
import os
import uuid
from typing import Any

import anyio
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.create import (
    ApiCreateRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


@lambda_exception_handler
async def async_create(event: dict[str, Any], context: Any) -> dict[str, Any]:
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    body = event.get("body", "")
    author_id = body.get("author_id", "")
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
        if author_id and not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or current_user.id == author_id
        ):
            return {
                "statusCode": 403,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
        else:
            body["author_id"] = current_user.id

    api = ApiCreateRecipe(**body)
    cmd = api.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 201,
        "body": json.dumps({"message": "Recipe created successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a recipe.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_create, event, context)
