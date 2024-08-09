import json

import src.contexts.iam.shared.endpoints.internal.get as iam_api
from src.contexts.products_catalog.shared.adapters.internal_providers.iam.api_schemas.user import (
    IAMUser,
)


class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="products_catalog")
        data = json.loads(response)
        if data.get("statusCode") != 200:
            return data
        data["body"] = IAMUser(**json.loads(data["body"])).to_domain()
        return data
