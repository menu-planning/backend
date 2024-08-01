from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.base_tag import (
    ApiTag,
)
from src.contexts.products_catalog.shared.domain.entities.tags import ParentCategory


class ApiParentCategory(ApiTag):
    """
    A Pydantic model representing and validating a parent category tag.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the tag.
        name (str): Name of the tag.
        author_id (str): Identifier of the tag's author.
        description (str, optional): Description of the tag.

    Methods:
        from_domain(domain_obj: ParentCategory) -> "ApiParentCategory":
            Creates an instance of `ApiParentCategory` from a domain model object.
        to_domain() -> ParentCategory:
            Converts the instance to a domain model object.
    """

    @classmethod
    def from_domain(cls, domain_obj: ParentCategory) -> "ApiParentCategory":
        """Creates an instance of `ApiParentCategory` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> ParentCategory:
        """Converts the instance to a domain model object."""
        return super().to_domain(ParentCategory)
