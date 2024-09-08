import json

import src.contexts.iam.shared.endpoints.internal.get as iam_api
from src.contexts.menu_planning.shared.adapters.internal_providers.iam.api_schemas.user import (
    IAMUser,
)
from src.logging.logger import logger


class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="menu_planning")
        logger.debug(f"Response from IAMProvider: {response}")
        if response.get("statusCode") != 200:
            return response
        user = IAMUser(**json.loads(response["body"])).to_domain()
        logger.debug(f"User from IAMProvider: {user}")
        return {"statusCode": 200, "body": user}
