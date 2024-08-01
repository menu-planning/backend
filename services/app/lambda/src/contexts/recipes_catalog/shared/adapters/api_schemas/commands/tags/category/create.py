from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.create import (
    ApiCreateTag,
)
from src.contexts.recipes_catalog.shared.domain.commands import CreateCategory


class ApiCreateCategory(ApiCreateTag):
    """A Pydantic model representing and validating the the data required
    to add a new category via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the category.
        author_id (str): The id of the user adding the category.
        privacy (Privacy, optional): Privacy setting of the category.
        description (str, optional): Detailed description of the category.

    Methods:
        to_domain() -> CreateCategory:
            Converts the instance to a domain model object for adding a category.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    def to_domain(self) -> CreateCategory:
        """Converts the instance to a domain model object for adding a category."""
        return super().to_domain(CreateCategory)
