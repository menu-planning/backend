from pydantic import BaseModel

from src.contexts.recipes_catalog.core.domain.commands.tag.create import \
    CreateTag


class ApiCreateTag(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new tag via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the tag.
        author_id (str): The id of the user adding the tag.
        key (str): The key of the tag.
        type (str): The type of the tag (eg. 'recipe', 'meal'...).

    Methods:
        to_domain() -> CreateTag:
            Converts the instance to a domain model object for creating a tag.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    value: str
    author_id: str
    key: str = 'tag'
    type: str = 'general'

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
            raise ValueError(f"Failed to convert ApiCreateTag to domain model: {e}")
