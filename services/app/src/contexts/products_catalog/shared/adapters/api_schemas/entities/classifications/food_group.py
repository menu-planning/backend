from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    FoodGroup,
)


class ApiFoodGroup(ApiClassification):
    """
    A Pydantic model representing and validating a food group classification.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the classification.
        name (str): Name of the classification.
        author_id (str): Identifier of the classifications's author.
        description (str, optional): Description of the classification.

    Methods:
        from_domain(domain_obj: FoodGroup) -> "ApiFoodGroup":
            Creates an instance of `ApiFoodGroup` from a domain model object.
        to_domain() -> FoodGroup:
            Converts the instance to a domain model object.
    """

    @classmethod
    def from_domain(cls, domain_obj: FoodGroup) -> "ApiFoodGroup":
        """Creates an instance of `ApiFoodGroup` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> FoodGroup:
        """Converts the instance to a domain model object."""
        return super().to_domain(FoodGroup)
