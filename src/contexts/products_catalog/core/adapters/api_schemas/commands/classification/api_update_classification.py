from typing import Any, ClassVar

from pydantic import BaseModel
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    UpdateClassification,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class _ApiAttributesToUpdateOnClassification(BaseModel):
    """API schema for classification attributes that can be updated.
    
    Attributes:
        name: Name of the classification.
        privacy: Privacy setting of the classification.
        description: Detailed description of the classification.
    """

    name: str | None = None
    privacy: Privacy | None = None
    description: str | None = None

    def to_domain(self) -> dict[str, Any]:
        """Convert API schema to domain update dictionary.
        
        Returns:
            Dictionary of attributes to update.
            
        Raises:
            ValidationConversionError: If conversion to domain model fails.
        """
        try:
            return {
                "name": self.name,
                "privacy": self.privacy,
                "description": self.description,
            }
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert _ApiAttributesToUpdateOnClassification to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e


class ApiUpdateClassification(BaseModel):
    """API schema for updating a product classification.
    
    Attributes:
        id: Identifier of the classification to update.
        updates: Attributes to update.
        command_type: Class variable specifying the domain command type.
    """

    id: str
    updates: _ApiAttributesToUpdateOnClassification

    command_type: ClassVar[type[UpdateClassification]]

    def to_domain(self) -> UpdateClassification:
        """Convert API schema to domain command.
        
        Returns:
            UpdateClassification domain command.
            
        Raises:
            ValidationConversionError: If conversion to domain model fails.
        """
        try:
            return self.command_type(
                id=self.id,
                updates=self.updates.to_domain()
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiUpdateClassification to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
