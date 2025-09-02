from src.contexts.recipes_catalog.core.domain.shared.commands.create import CreateTag
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.adapters.api_schemas.fields import (
    TagKey,
    TagType,
    TagValue,
)


class ApiCreateTag(BaseApiCommand[CreateTag]):
    """
    A Pydantic model representing and validating the data required
    to add a new tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        value (str): Value of the tag.
        author_id (str): ID of the user adding the tag.
        key (str): Key of the tag.
        type (str): Type of the tag (e.g. 'recipe', 'meal'...).

    Methods:
        to_domain() -> CreateTag:
            Converts the instance to a domain model object for creating a tag.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    value: TagValue
    author_id: UUIDIdRequired
    key: TagKey = "tag"
    type: TagType = "general"

    def to_domain(self) -> CreateTag:
        """Converts the instance to a domain model object for creating a tag."""
        try:
            return CreateTag(
                key=self.key,
                value=self.value,
                author_id=self.author_id,
                type=self.type,
            )
        except Exception as e:
            error_msg = f"Failed to convert ApiCreateTag to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
