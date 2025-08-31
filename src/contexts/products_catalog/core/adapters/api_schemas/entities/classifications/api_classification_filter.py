from pydantic import BaseModel
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    CreatedAtValue,
)


class ApiClassificationFilter(BaseModel):
    """
    A Pydantic model representing and validating a filter for recipe classifications.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the classification.
        author_id (str, optional): Identifier of the classification's author.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary for use in a domain model object.
    """

    name: str | None = None
    author_id: str | None = None
    created_at_gte: CreatedAtValue | None = None
    created_at_lte: CreatedAtValue | None = None
    skip: int | None = None
    limit: int | None = 100
    sort: str | None = "-created_at"
