from typing import Any

from pydantic import BaseModel

from src.contexts.products_catalog.shared.domain.commands.classifications.base_classes import (
    UpdateClassification,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class _ApiAttributesToUpdateOnClassification(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update attributes of a product classification via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the classification.
        privacy (Privacy, optional): Privacy setting of the classification.
        description (str, optional): Detailed description of the classification.

    Methods:
        to_domain() -> dict[str, Any]:
            Converts the instance to a domain model object for updating a product classification.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str | None = None
    privacy: Privacy | None = None
    description: str | None = None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a domain model object for updating a product classification."""
        try:
            return {
                "name": self.name,
                "privacy": self.privacy,
                "description": self.description,
            }
        except Exception as e:
            raise ValueError(
                f"Failed to convert _ApiAttributesToUpdateOnClassification to domain model: {e}"
            )


class ApiUpdateClassification(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a product classification via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Identifier of the classification to update.
        updates (ApiAttributesToUpdateOnRecipe): Attributes to update.

    Methods:
        to_domain() -> UpdateRecipe:
            Converts the instance to a domain model object for updating a product.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    id: str
    updates: _ApiAttributesToUpdateOnClassification

    def to_domain(
        self, classification_type: type[UpdateClassification]
    ) -> UpdateClassification:
        """Converts the instance to a domain model object for updating a category."""
        try:
            return classification_type(id=self.id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiUpdateClassification to domain model: {e}"
            )
