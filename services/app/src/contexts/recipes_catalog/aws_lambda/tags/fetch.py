import json
import os
import uuid
from typing import Any, Type

import anyio
from src.contexts.recipes_catalog.aws_lambda import utils
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.base_class import (
    ApiTag,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.category import (
    ApiCategory,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.meal_planning import (
    ApiMealPlanning,
)
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import RecipeTagTypeURI
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.allergen import (
    ApiAllergen,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.cuisine import (
    ApiCuisine,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.flavor import (
    ApiFlavor,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.texture import (
    ApiTexture,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for tags.
    """
    logger.debug(f"Event received {event}")
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        logger.debug(f"Fetching tags for user {user_id}")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
    else:
        current_user = SeedUser(id="localstack_user")

    tag_config: dict[RecipeTagTypeURI, tuple[str, Type[ApiTag]]] = {
        RecipeTagTypeURI.CATEGORIES: ("categories", ApiCategory),
        RecipeTagTypeURI.MEAL_PLANNING: ("meal_plannings", ApiMealPlanning),
        RecipeTagTypeURI.ALLERGENS: ("allergens", ApiAllergen),
        RecipeTagTypeURI.CUISINES: ("cuisines", ApiCuisine),
        RecipeTagTypeURI.FLAVORS: ("flavors", ApiFlavor),
        RecipeTagTypeURI.TEXTURES: ("textures", ApiTexture),
    }

    tag_type = event.get("pathParameters", {}).get("tag_type")
    if tag_type not in tag_config:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Invalid tag type provided."}),
        }

    bus: MessageBus = Container().bootstrap()
    repo_name, api_schema_class = tag_config[tag_type]
    if (
        tag_type == RecipeTagTypeURI.CATEGORIES
        or tag_type == RecipeTagTypeURI.MEAL_PLANNING
    ):
        return await utils.read_tags(
            event=event,
            current_user=current_user,
            uow_repo_name=repo_name,
            bus=bus,
            api_schema_class=api_schema_class,
        )
    else:
        return await utils.read_name_tags(
            event=event,
            uow_repo_name=repo_name,
            bus=bus,
            api_schema_class=api_schema_class,
        )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for tags.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)
