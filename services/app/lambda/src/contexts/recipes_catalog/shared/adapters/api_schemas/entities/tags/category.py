from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.base_class import (
    ApiTag,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags import Category


class ApiCategory(ApiTag):
    """
    A Pydantic model representing and validating a recipe category tag.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the tag.
        name (str): Name of the tag.
        author_id (str): Identifier of the tag's author.
        privacy (Privacy): Privacy setting of the tag.
        description (str, optional): Description of the tag.

    Methods:
        from_domain(domain_obj: Category) -> "ApiCategory":
            Creates an instance of `ApiCategory` from a domain model object.
        to_domain() -> Category:
            Converts the instance to a domain model object.
    """

    @classmethod
    def from_domain(cls, domain_obj: Category) -> "ApiCategory":
        """Creates an instance of `ApiCategory` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> Category:
        """Converts the instance to a domain model object."""
        return super().to_domain(Category)
