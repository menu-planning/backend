import json
import os
import uuid
from typing import Any, Type

import anyio
from src.contexts.recipes_catalog.aws_lambda import utils
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.meal_planning.delete import (
    DeleteMealPlanning,
)
from src.contexts.recipes_catalog.shared.domain.enums import RecipeTagTypeURI
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """ "
    Lambda function handler to delete a tag.
    """
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
    else:
        current_user = SeedUser(id="localstack-user")

    tag_config: dict[RecipeTagTypeURI, tuple[str, Type[DeleteTag]]] = {
        RecipeTagTypeURI.MEAL_PLANNING: ("meal_plannings", DeleteMealPlanning),
    }

    tag_type = event.get("pathParameters", {}).get("tag_type")
    id = event.get("pathParameters", {}).get("id")

    if tag_type not in tag_config:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Invalid tag type provided."}),
        }

    bus: MessageBus = Container().bootstrap()
    repo_name, delete_cmd_class = tag_config[tag_type]
    await utils.delete_tag(
        id,
        current_user,
        repo_name,
        delete_cmd_class,
        bus,
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a tag.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)
