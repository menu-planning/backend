import json

import src.contexts.iam.aws_lambda.internal.get as iam_api
from src.contexts.products_catalog.fastapi.internal_providers.iam.api_schemas.user import (
    IAMUser,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser


class IAMProvider:
    @staticmethod
    async def get(id: str) -> dict:
        response = await iam_api.get(id=id, caller_context="products_catalog")
        data = json.loads(response)
        if data.get("statusCode") != 200:
            return data
        data["body"] = IAMUser(**json.loads(data["body"])).to_domain()
        return data
