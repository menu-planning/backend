from pydantic import BaseModel, field_validator
from src.config.pagination_config import get_pagination_settings
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    CreatedAtValue,
)


class ApiClassificationFilter(BaseModel):
    """API schema for filtering classifications.

    Attributes:
        name: Name of the classification.
        author_id: Identifier of the classification's author.
        created_at_gte: Filter classifications created after this date.
        created_at_lte: Filter classifications created before this date.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        sort: Sort order for results.
    """

    name: str | None = None
    author_id: str | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    skip: int | None = None
    limit: int | None = get_pagination_settings().CLASSIFICATIONS
    sort: str | None = "-created_at"

    @field_validator("limit")
    @classmethod
    def check_limit(cls, value: int | None) -> int:
        if value is None or value < 1:
            return 50
        return min(value, 200)
