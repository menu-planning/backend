from typing import Any, Dict
from pydantic import field_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseCommand
from src.contexts.recipes_catalog.core.domain.commands.tag.create import CreateTag
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDId
from src.db.base import SaBase
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.tag.fields import (
    TagValue,
    TagKey,
    TagType,
)


class ApiCreateTag(BaseCommand[CreateTag, SaBase]):
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
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    value: TagValue
    author_id: UUIDId
    key: TagKey = 'tag'
    type: TagType = 'general'

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
