from datetime import datetime
from typing import Any, ClassVar

import src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification_fields as fields
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiEntity,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiClassification(BaseApiEntity[Classification, ClassificationSaModel]):
    """API schema for classification entity.

    Attributes:
        name: Name of the classification.
        author_id: Identifier of the classification's author.
        description: Description of the classification.
        entity_type: Class variable specifying the domain entity type.
        entity_type_name: Class variable specifying the entity type name.
    """

    name: fields.ClassificationNameRequired
    author_id: fields.ClassificationAuthorIdRequired
    description: fields.ClassificationDescriptionOptional

    entity_type: ClassVar[type[Classification]] = Classification
    entity_type_name: ClassVar[str] = "classification"

    @classmethod
    def from_domain(cls, domain_obj: Classification) -> "ApiClassification":
        """Create API schema instance from domain object.

        Args:
            domain_obj: Domain classification object.

        Returns:
            ApiClassification instance.

        Raises:
            ValidationConversionError: If conversion from domain fails.
        """
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
            raise ValidationConversionError(
                f"Failed to build ApiClassification from domain instance: {e}",
                schema_class=cls,
                conversion_direction="domain_to_api",
                source_data={"domain_obj": str(domain_obj)},
                validation_errors=[str(e)],
            ) from e

    def to_domain(self) -> Classification:
        """Convert API schema to domain object.

        Returns:
            Classification domain object.

        Raises:
            ValidationConversionError: If conversion to domain fails.
        """
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
            raise ValidationConversionError(
                f"Failed to convert ApiClassification to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_orm_model(cls, orm_model: ClassificationSaModel) -> "ApiClassification":
        """Convert ORM model to API schema instance.

        Args:
            orm_model: SQLAlchemy classification model.

        Returns:
            ApiClassification instance.
        """
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

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM model kwargs.

        Returns:
            Dictionary of kwargs for ORM model creation.
        """
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
