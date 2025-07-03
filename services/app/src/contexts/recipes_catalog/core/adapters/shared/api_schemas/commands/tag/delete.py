from src.contexts.recipes_catalog.core.domain.shared.commands.delete import DeleteTag
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId


class ApiDeleteTag(BaseApiCommand[DeleteTag]):
    """
    A Pydantic model representing and validating the data required
    to delete a tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): ID of the tag to delete.

    Methods:
        to_domain() -> DeleteTag:
            Converts the instance to a domain model object for deleting a tag.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    id: UUIDId

    def to_domain(self) -> DeleteTag:
        """Converts the instance to a domain model object for deleting a tag."""
        try:
            return DeleteTag(id=self.id)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDeleteTag to domain model: {e}")
