import json

import src.contexts.iam.core.endpoints.internal.get as iam_api
from src.contexts.products_catalog.core.adapters.internal_providers.iam.api_schemas.user import (
    IAMUser,
)
from src.logging.logger import logger


class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="products_catalog")
        logger.debug(f"Response from IAMProvider: {response}")
        if response.get("statusCode") != 200:
            return response
        user = IAMUser(**json.loads(str(response["body"]))).to_domain()
        logger.debug(f"User from IAMProvider: {user}")
        return {"statusCode": 200, "body": user}
