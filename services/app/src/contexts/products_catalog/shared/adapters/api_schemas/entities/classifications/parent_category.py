from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    ParentCategory,
)


class ApiParentCategory(ApiClassification):
    """
    A Pydantic model representing and validating a parent category classification.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the classification.
        name (str): Name of the classification.
        author_id (str): Identifier of the classifications's author.
        description (str, optional): Description of the classification.

    Methods:
        from_domain(domain_obj: ParentCategory) -> "ApiParentCategory":
            Creates an instance of `ApiParentCategory` from a domain model object.
        to_domain() -> ParentCategory:
            Converts the instance to a domain model object.
    """

    @classmethod
    def from_domain(cls, domain_obj: ParentCategory) -> "ApiParentCategory":
        """Creates an instance of `ApiParentCategory` from a domain model object."""
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            description=domain_obj.description,
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    def to_domain(self) -> ParentCategory:
        """Converts the instance to a domain model object."""
        return ParentCategory(
            id=self.id,
            name=self.name,
            author_id=self.author_id,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )
