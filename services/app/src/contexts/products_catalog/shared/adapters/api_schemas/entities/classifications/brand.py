from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Brand


class ApiBrand(ApiClassification):
    """
    A Pydantic model representing and validating a brand classification.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the classification.
        name (str): Name of the classification.
        author_id (str): Identifier of the classification's author.
        description (str, optional): Description of the classification.

    Methods:
        from_domain(domain_obj: Brand) -> "ApiBrand":
            Creates an instance of `ApiBrand` from a domain model object.
        to_domain() -> Brand:
            Converts the instance to a domain model object.
    """

    @classmethod
    def from_domain(cls, domain_obj: Brand) -> "ApiBrand":
        """Creates an instance of `ApiBrand` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> Brand:
        """Converts the instance to a domain model object."""
        return super().to_domain(Brand)
