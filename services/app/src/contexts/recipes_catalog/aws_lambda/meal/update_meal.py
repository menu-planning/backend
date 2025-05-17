import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.meal.update import (
    ApiUpdateMeal,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.meal.meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug(f"Event received {event}")
    body = json.loads(event.get("body", ""))
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        # response: dict = await IAMProvider.get(user_id)
        # if response.get("statusCode") != 200:
        #     return response
        
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    meal_id = event.get("pathParameters", {}).get("id")
    # async with bus.uow as uow:
    #     try:
    #         await uow.meals.get(meal_id)
    #     except EntityNotFoundException:
    #         return {
    #             "statusCode": 403,
    #             "headers": CORS_headers,
    #             "body": json.dumps({"message": f"Meal {meal_id} not in database."}),
    #         }

    for tag in body.get("tags", []):
        tag["author_id"] = user_id
        tag["type"] = "meal"

    for recipe in body.get("recipes", []):
        for tag in recipe.get("tags", []):
            tag["author_id"] = body["author_id"]
            tag["type"] = "recipe"

    logger.debug(f"Body {body}")
    logger.debug(f"ApiMeal {ApiMeal(**body)}")
    api_meal = ApiMeal(**body)
    logger.debug(f"Api {ApiUpdateMeal.from_api_meal(api_meal)}")
    api = ApiUpdateMeal.from_api_meal(api_meal)
    logger.debug(f"updating recipe {api}")

    cmd = api.to_domain()
    await bus.handle(cmd)
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Meal updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a meal by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
