import json

import src.contexts.iam.core.endpoints.internal.get as iam_api
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api_schemas.api_user import (
    ApiUser,
)
from src.logging.logger import logger


class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="recipes_catalog")
        if response.get("statusCode") != 200:
            return response
        user = ApiUser.model_validate_json(response["body"]) # type: ignore
        logger.debug(f"User from IAMProvider: {user}")
        return {"statusCode": 200, "body": user}
