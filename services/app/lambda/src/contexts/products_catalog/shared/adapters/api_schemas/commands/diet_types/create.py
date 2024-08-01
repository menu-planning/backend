from pydantic import BaseModel
from src.contexts.products_catalog.shared.domain.commands.diet_types.create import (
    CreateDietType,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiCreateDietType(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new DietType via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the DietType.
        author_id (str): The id of the user adding the DietType.
        privacy (Privacy, optional): Privacy setting of the DietType.
        description (str, optional): Detailed description of the DietType.

    Methods:
        to_domain() -> CreateDietType:
            Converts the instance to a domain model object for adding a DietType.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    author_id: str | None = None
    privacy: Privacy = Privacy.PRIVATE
    description: str | None = None

    def to_domain(self) -> CreateDietType:
        """Converts the instance to a domain model object for adding a diet type."""
        try:
            return CreateDietType(
                name=self.name,
                author_id=self.author_id,
                privacy=self.privacy,
                description=self.description,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiCreateDietType to domain model: {e}"
            )
