from pydantic import BaseModel
from src.contexts.products_catalog.shared.adapters.api_schemas.pydantic_validators import (
    CreatedAtValue,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    Classification,
)


class ApiClassification(BaseModel):
    """
    A Pydantic model representing and validating a recipe classification.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the classification.
        name (str): Name of the classification.
        author_id (str): Identifier of the recipes's author.
        privacy (Privacy): Privacy setting of the classification.
        description (str, optional): Description of the classification.

    Methods:
        from_domain(domain_obj: Classification) -> "ApiClassification":
            Creates an instance of `ApiClassification` from a domain model object.
        to_domain() -> Classification:
            Converts the instance to a domain model object.
    """

    id: str
    name: str
    author_id: str
    description: str | None = None
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    discarded: bool = False
    version: int = 1

    @classmethod
    def from_domain(
        cls, domain_obj: Classification
    ) -> "ApiClassification":
        """Creates an instance of `ApiClassification` from a domain model object."""
        try:
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
        except Exception as e:
            raise ValueError(
                f"Failed to build ApiClassification from domain instance: {e}"
            )

    def to_domain(self) -> Classification:
        """Converts the instance to a domain model object."""
        try:
            return Classification(
                id=self.id,
                name=self.name,
                author_id=self.author_id,
                description=self.description,
                created_at=self.created_at,
                updated_at=self.updated_at,
                discarded=self.discarded,
                version=self.version,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiClassification to domain model: {e}"
            )
