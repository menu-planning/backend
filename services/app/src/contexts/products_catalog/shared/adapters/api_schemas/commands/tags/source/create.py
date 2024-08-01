from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.base_class import (
    ApiCreateTag,
)
from src.contexts.products_catalog.shared.domain.commands import CreateSource


class ApiCreateSource(ApiCreateTag):
    """A Pydantic model representing and validating the the data required
    to add a new source via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the source.
        author (ApiUser): The user adding the source.
        description (str, optional): Detailed description of the source.

    Methods:
        to_domain() -> CreateSource:
            Converts the instance to a domain model object for adding a source.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    def to_domain(self) -> CreateSource:
        """Converts the instance to a domain model object for adding a source."""
        return super().to_domain(CreateSource)
