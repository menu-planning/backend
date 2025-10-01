"""API filter model for querying tags."""

from pydantic import BaseModel, field_validator

from src.config.pagination_config import get_pagination_settings


class ApiTagFilter(BaseModel):
    """API schema for tag filter operations.

    Attributes:
        key: Tag key filter, single value or list.
        value: Tag value filter, single value or list.
        author_id: Author ID filter, single value or list.
        type: Tag type filter, single value or list.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return, defaults to 100.
        sort: Sort field with optional direction prefix, defaults to "-key".

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Frozen model for immutability at API boundary.
    """

    model_config = {"frozen": True}

    key: str | list[str] |  None = None
    value: str | list[str] |  None = None
    author_id: str |list[str] | None = None
    type: str | list[str] | None = None
    skip: int | None = None
    limit: int | None = get_pagination_settings().TAGS
    sort: str | None = "-key"

    @field_validator("limit")
    @classmethod
    def check_limit(cls, value: int | None) -> int:
        if value is None or value < 1:
            return 100
        return min(value, 500)

    def to_domain(self) -> dict:
        """Return a dictionary suitable for domain-layer queries.

        Returns:
            Mapping excluding None values.
        """
        return self.model_dump(exclude_none=True)
