from typing import Any

from pydantic import BaseModel
from src.contexts.recipes_catalog.shared.domain.commands.diet_types.update import (
    UpdateDietType,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class AttributesToUpdateOnDietType(BaseModel):
    """
    A Pydantic model representing and validating the data required to update a DietType via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the DietType.
        privacy (Privacy, optional): Privacy setting of the DietType.
        description (str, optional): Detailed description of the DietType.

    Methods:
        to_domain() -> UpdateDietType:
            Converts the instance to a domain model object for updating a DietType.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str | None = None
    privacy: Privacy | None = None
    description: str | None = None

    def to_domain(self) -> UpdateDietType:
        """Converts the instance to a domain model object for updating a DietType."""
        try:
            return UpdateDietType(
                name=self.name,
                privacy=self.privacy,
                description=self.description,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert AttributesToUpdateOnDietType to domain model: {e}"
            )


class ApiUpdateDietType(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a DietType via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Identifier of the DietType to update.
        updates (AttributesToUpdateOnDietType): Attributes to update.

    Methods:
        to_domain() -> UpdateDietType:
            Converts the instance to a domain model object for updating a DietType.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    id: str
    updates: AttributesToUpdateOnDietType

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a domain model object for updating a DietType."""
        try:
            return UpdateDietType(
                diet_type_id=self.id, updates=self.updates.to_domain()
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateDietTypeto domain model: {e}")
