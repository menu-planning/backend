from pydantic import BaseModel, model_validator
from src.contexts.recipes_catalog.shared.adapters.repositories.tags import (
    tag as tag_repo,
)
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiTagFilter(BaseModel):
    """
    A Pydantic model representing and validating the data required to filter
    tags.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the tag.
        author_id (str, optional): Identifier of the tag's author.
        privacy (Privacy, optional): Privacy setting of the tag.
        description (str, optional): Description of the tag.

    Methods:
        to_domain() -> TagFilter:
            Converts the instance to a domain model object for filtering tags.
    """

    name: str | None = None
    author_id: str | None = None
    privacy: Privacy | None = None
    description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values):
        """Ensures that only allowed filters are used."""
        allowed_filters = []
        for mapper in tag_repo.TagRepo.filter_to_column_mappers:
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
