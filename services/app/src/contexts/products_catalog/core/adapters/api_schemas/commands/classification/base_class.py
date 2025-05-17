from typing import ClassVar
from pydantic import BaseModel

from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiCreateClassification(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new classification via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the classification.
        author_id (str): The id of the user adding the classification.
        privacy (Privacy, optional): Privacy setting of the classification.
        description (str, optional): Detailed description of the classification.

    Methods:
        to_domain() -> Createclassification:
            Converts the instance to a domain model object for adding a classification.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    author_id: str
    description: str | None = None

    command_type: ClassVar[type[CreateClassification]]

    def to_domain(self) -> CreateClassification:
        """Converts the instance to a domain model object for adding a classification."""
        try:
            return self.command_type(
                name=self.name,
                author_id=self.author_id,
                description=self.description,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiCreateclassification to domain model: {e}"
            )
