import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.meal.create_meal import (
    ApiCreateMeal,
)
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug(f"Event received {event}")

    body = json.loads(event.get("body", ""))

    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    response: dict = await IAMProvider.get(user_id)

    logger.debug(f"Response from IAMProvider {response}")

    if response.get("statusCode") != 200:
        return response
    current_user: SeedUser = response["body"]

    author_id = body.get("author_id", "")
    if author_id and not (
        current_user.has_permission(Permission.MANAGE_MEALS)
        or current_user.id == author_id
    ):
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps(
                {"message": "User does not have enough privilegies."}
            ),
        }
    else:
        body["author_id"] = current_user.id

    for tag in body.get("tags", []):
        tag["author_id"] = body["author_id"]
        tag["type"] = "meal"

    for recipe in body.get("recipes", []):
        for tag in recipe.get("tags", []):
            tag["author_id"] = body["author_id"]
            tag["type"] = "recipe"

    logger.debug(f"Body {body}")
    logger.debug(f"Api {ApiCreateMeal(**body)}")
    api = ApiCreateMeal(**body)
    cmd = api.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Meal created successfully",
            "meal_id": cmd.meal_id
        }),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a meal.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
