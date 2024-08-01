from abc import abstractmethod
from typing import Any

from pydantic import BaseModel
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    UpdateTag,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class _ApiAttributesToUpdateOnTag(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update attributes of a recipe tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the tag.
        privacy (Privacy, optional): Privacy setting of the tag.
        description (str, optional): Detailed description of the tag.

    Methods:
        to_domain() -> dict[str, Any]:
            Converts the instance to a domain model object for updating a recipe tag.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str | None = None
    privacy: Privacy | None = None
    description: str | None = None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a domain model object for updating a recipe tag."""
        try:
            return {
                "name": self.name,
                "privacy": self.privacy,
                "description": self.description,
            }
        except Exception as e:
            raise ValueError(
                f"Failed to convert _ApiAttributesToUpdateOnTag to domain model: {e}"
            )


class ApiUpdateTag(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a recipe tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Identifier of the tag to update.
        updates (ApiAttributesToUpdateOnTag): Attributes to update.

    Methods:
        to_domain() -> UpdateTag:
            Converts the instance to a domain model object for updating a Tag.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    id: str
    updates: _ApiAttributesToUpdateOnTag

    def to_domain(self, tag_type: type[UpdateTag]) -> UpdateTag:
        """Converts the instance to a domain model object for updating a category."""
        try:
            return tag_type(id=self.id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateTag to domain model: {e}")
