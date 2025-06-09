import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.domain.meal.commands.delete_meal import DeleteMeal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        meal_id = event.get("pathParameters", {}).get("id")
        try:
            meal = await uow.meals.get(meal_id)
        except EntityNotFoundException:
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps({"message": f"Meal {meal_id} not in database."}),
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
            current_user.has_permission(Permission.MANAGE_MEALS)
            or meal.author_id == current_user.id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
    cmd = DeleteMeal(meal_id=meal_id)
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
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
