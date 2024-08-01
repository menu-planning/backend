from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.base_class import (
    ApiTag,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags import MealPlanning


class ApiMealPlanning(ApiTag):
    """
    A Pydantic model representing and validating a meal planning tag.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the tag.
        name (str): Name of the tag.
        author_id (str): Identifier of the tag's author.
        privacy (Privacy): Privacy setting of the tag.
        description (str, optional): Description of the tag.

    Methods:
        from_domain(domain_obj: MealPlanning) -> "ApiMealPlanning":
            Creates an instance of `ApiMealPlanning` from a domain model object.
        to_domain() -> MealPlanning:
            Converts the instance to a domain model object.
    """

    @classmethod
    def from_domain(cls, domain_obj: MealPlanning) -> "ApiMealPlanning":
        """Creates an instance of `ApiMealPlanning` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> MealPlanning:
        """Converts the instance to a domain model object."""
        return super().to_domain(MealPlanning)
