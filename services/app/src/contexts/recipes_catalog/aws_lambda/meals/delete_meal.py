import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.commands.recipe.delete import \
    DeleteRecipe
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import \
    EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    recipe_id = event.get("pathParameters", {}).get("id")
    async with bus.uow as uow:
        try:
            meal = await uow.meals.get(recipe_id)
        except EntityNotFoundException:
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps({"message": f"Recipe {recipe_id} not in database."}),
            }
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
        if not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or meal.author_id == current_user.id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
    cmd = DeleteRecipe(recipe_id=recipe_id)
    await bus.handle(cmd)
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Meal deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a meal.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)
