from typing import ClassVar

from pydantic import BaseModel
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiCreateClassification(BaseModel):
    """API schema for creating a new classification.

    Attributes:
        name: Name of the classification.
        author_id: The id of the user adding the classification.
        description: Detailed description of the classification.
        command_type: Class variable specifying the domain command type.
    """

    name: str
    author_id: str
    description: str | None = None

    command_type: ClassVar[type[CreateClassification]]

    def to_domain(self) -> CreateClassification:
        """Convert API schema to domain command.

        Returns:
            CreateClassification domain command.

        Raises:
            ValidationConversionError: If conversion to domain model fails.
        """
        try:
            return self.command_type(
                name=self.name,
                author_id=self.author_id,
                description=self.description,
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiCreateclassification to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
