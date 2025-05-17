from pydantic import BaseModel, model_validator

from src.contexts.recipes_catalog.core.adapters.api_schemas.pydantic_validators import (
    CreatedAtValue,
)
from src.contexts.recipes_catalog.core.adapters.repositories.client import ClientRepo
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository


class ApiClientFilter(BaseModel):
    id: str | list[str] | None = None
    menu_id: str | list[str] | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-created_at"

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in ClientRepo.filter_to_column_mappers or []:
            allowed_filters.extend(mapper.filter_key_to_column_name.keys())
        allowed_filters.extend(
            [
                "discarded",
                "skip",
                "limit",
                "sort",
                "created_at",
            ]
        )
        for k in values.keys():
            if SaGenericRepository.remove_postfix(k) not in allowed_filters:
                raise ValueError(f"Invalid filter: {k}")
        return values
