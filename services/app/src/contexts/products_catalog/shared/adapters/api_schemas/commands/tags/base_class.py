from pydantic import BaseModel
from src.contexts.products_catalog.shared.domain.commands.tags.base_classes import (
    CreateTag,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiCreateTag(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the tag.
        author_id (str): The id of the user adding the tag.
        privacy (Privacy, optional): Privacy setting of the tag.
        description (str, optional): Detailed description of the tag.

    Methods:
        to_domain() -> CreateTag:
            Converts the instance to a domain model object for adding a tag.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    author_id: str | None = None
    privacy: Privacy = Privacy.PRIVATE
    description: str | None = None

    def to_domain(self, cmd_type: type[CreateTag]) -> CreateTag:
        """Converts the instance to a domain model object for adding a tag."""
        try:
            return cmd_type(
                name=self.name,
                author_id=self.author_id,
                privacy=self.privacy,
                description=self.description,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateTag to domain model: {e}")
