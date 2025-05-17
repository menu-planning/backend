from pydantic import BaseModel
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.user import (
    ApiUser,
)
from src.contexts.recipes_catalog.core.domain.value_objects.user import User

from .role import ApiRole


class IAMUser(BaseModel):
    id: str
    roles: list[ApiRole]
    discarded: bool
    version: int

    def to_domain(self) -> User:
        try:
            return ApiUser(
                **self.model_dump(exclude={"discarded", "version"})
            ).to_domain()
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e

    def to_local_context_api_user(self) -> ApiUser:
        try:
            return ApiUser.from_domain(self.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
