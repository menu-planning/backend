from pydantic import BaseModel, field_validator, model_validator
from src.contexts.recipes_catalog.core.adapters.client.repositories.menu_repository import (
    MenuRepo,
)
from src.contexts.recipes_catalog.core.adapters.shared.parse_tags import parse_tags
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    CreatedAtValue,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)
from src.config.pagination_config import get_pagination_settings


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
    limit: int | None = get_pagination_settings().MENUS
    sort: str | None = "-created_at"
    # TODO add full text search

    @field_validator("limit")
    @classmethod
    def check_limit(cls, value: int | None) -> int:
        if value is None or value < 1:
            return 50
        return min(value, 100)

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        for key, value in data.items():
            if key in ["tags", "tags_not_exists"]:
                data[key] = parse_tags(value)
            elif isinstance(value, str) and "|" in value:
                data[key] = [i.strip() for i in value.split("|")]
        return data

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in MenuRepo.filter_to_column_mappers or []:
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
        for k in values:
            if SaGenericRepository.remove_postfix(k) not in allowed_filters:
                error_msg = f"Invalid filter: {k}"
                raise ValidationConversionError(
                    error_msg,
                    schema_class=cls,
                    conversion_direction="filter_validation",
                    source_data={"filter_key": k, "allowed_filters": allowed_filters},
                )
        return values
