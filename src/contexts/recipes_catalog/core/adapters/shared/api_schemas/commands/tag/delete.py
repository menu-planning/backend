from src.contexts.recipes_catalog.core.domain.shared.commands.delete import DeleteTag
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


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
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    id: UUIDIdRequired

    def to_domain(self) -> DeleteTag:
        """Converts the instance to a domain model object for deleting a tag."""
        try:
            return DeleteTag(id=self.id)
        except Exception as e:
            error_msg = f"Failed to convert ApiDeleteTag to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
