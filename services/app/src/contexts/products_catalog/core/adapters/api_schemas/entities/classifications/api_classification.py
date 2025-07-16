from typing import Any, Dict, ClassVar
from datetime import datetime

from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import ClassificationSaModel
from src.contexts.products_catalog.core.domain.entities.classification import Classification
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
import src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_fields as fields


class ApiClassification(BaseApiEntity[Classification, ClassificationSaModel]):
    """
    A Pydantic model representing and validating a classification.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the classification.
        name (str): Name of the classification.
        author_id (str): Identifier of the classification's author.
        description (str, optional): Description of the classification.

    Methods:
        from_domain(domain_obj: Classification) -> "ApiClassification":
            Creates an instance of `ApiClassification` from a domain model object.
        to_domain() -> Classification:
            Converts the instance to a domain model object.
        from_orm_model(orm_model: ClassificationSaModel) -> "ApiClassification":
            Creates an instance from an ORM model.
        to_orm_kwargs() -> Dict[str, Any]:
            Converts the instance to ORM model kwargs.
    """

    name: fields.ClassificationNameRequired
    author_id: fields.ClassificationAuthorIdRequired
    description: fields.ClassificationDescriptionOptional

    entity_type: ClassVar[type[Classification]] = Classification
    entity_type_name: ClassVar[str] = "classification"

    @classmethod
    def from_domain(cls, domain_obj: Classification) -> "ApiClassification":
        """Creates an instance of `ApiClassification` from a domain model object."""
        try:
            return cls(
                id=domain_obj.id,
                name=domain_obj.name,
                author_id=domain_obj.author_id,
                description=domain_obj.description,
                created_at=domain_obj.created_at or datetime.now(),
                updated_at=domain_obj.updated_at or datetime.now(),
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
            return self.entity_type(
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

    @classmethod
    def from_orm_model(cls, orm_model: ClassificationSaModel) -> "ApiClassification":
        """Convert an ORM model to an API schema instance."""
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            author_id=orm_model.author_id,
            description=orm_model.description,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            discarded=orm_model.discarded,
            version=orm_model.version,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs."""
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discarded": self.discarded,
            "version": self.version,
            "type": self.entity_type_name,
        }
