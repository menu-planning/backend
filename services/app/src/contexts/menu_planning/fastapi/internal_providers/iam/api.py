import json
from typing import Annotated

from fastapi import Depends
from src.contexts.iam.fastapi.internal import internal as iam_api
from src.contexts.seedwork.shared.adapters.api_schemas.value_ojbects.user import (
    ApiSeedUser,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser

from .api_schemas.user import IAMUser


class IAMProvider:
    @staticmethod
    async def get(id: str) -> SeedUser:
        user = await iam_api.get(id=id, caller_context="menu_planning")
        return IAMUser(**json.loads(user)).to_domain()

    @staticmethod
    def current_active_user(
        user_data: Annotated[
            SeedUser, Depends(iam_api.CurrentActiveUserWithContext("menu_planning"))
        ]
    ) -> ApiSeedUser:
        return IAMUser(**json.loads(user_data)).to_domain()
