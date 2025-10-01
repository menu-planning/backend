from pydantic import BaseModel, field_validator, model_validator
from src.config.pagination_config import get_pagination_settings
from src.contexts.recipes_catalog.core.adapters.client.repositories.client_repository import (
    ClientRepo,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    CreatedAtValue,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)


class ApiClientFilter(BaseModel):
    id: str | list[str] | None = None
    menu_id: str | list[str] | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    skip: int | None = None
    limit: int | None = get_pagination_settings().CLIENTS
    sort: str | None = "-created_at"

    @field_validator("limit")
    @classmethod
    def check_limit(cls, value: int | None) -> int:
        if value is None or value < 1:
            return 50
        return min(value, 100)

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
        for k in values:
            if SaGenericRepository.remove_postfix(k) not in allowed_filters:
                raise ValidationConversionError(
                    f"Invalid filter: {k}",
                    schema_class=cls,
                    conversion_direction="filter_validation",
                    source_data={"filter_key": k, "allowed_filters": allowed_filters},
                )
        return values
