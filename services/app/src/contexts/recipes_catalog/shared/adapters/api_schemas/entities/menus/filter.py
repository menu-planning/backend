from pydantic import BaseModel, model_validator
from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    CreatedAtValue,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.utils import parse_tags
from src.contexts.recipes_catalog.shared.adapters.repositories import menu as menu_repo
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiMenuFilter(BaseModel):
    id: str | list[str] | None = None
    author_id: str | list[str] | None = None
    client_id: str | list[str] | None = None
    tags: str | None = None
    description: str | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    discarded: bool | None = False
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-created_at"
    # TODO add full text search

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if key == "tags":
                data[key] = parse_tags(value)
            elif isinstance(value, str) and "|" in value:
                data[key] = value.split("|")
        return data

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in menu_repoMenuRepo.filter_to_column_mappers:
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
            if SaGenericRepository.removePostfix(k) not in allowed_filters:
                raise ValueError(f"Invalid filter: {k}")
        return values
