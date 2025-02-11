from pydantic import BaseModel
from src.contexts.recipes_catalog.shared.domain.commands.tags.delete import DeleteTag


class ApiDeleteTag(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to delete a tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): The id of the tag.

    Methods:
        to_domain() -> CreateTag:
            Converts the instance to a domain model object for deleting a tag.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    id: str

    def to_domain(self) -> DeleteTag:
        """Converts the instance to a domain model object for deleting a tag."""
        try:
            return DeleteTag(
                id=self.id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDeleteTag to domain model: {e}")
