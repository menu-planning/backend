from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.create import (
    ApiCreateTag,
)
from src.contexts.recipes_catalog.shared.domain.commands import CreateMealPlanning


class ApiCreateMealPlanning(ApiCreateTag):
    """A Pydantic model representing and validating the the data required
    to add a new meal planning via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the meal planning.
        author_id (str): The id of user adding the meal planning.
        privacy (Privacy, optional): Privacy setting of the meal planning.
        description (str, optional): Detailed description of the meal planning.

    Methods:
        to_domain() -> CreateMealPlanning:
            Converts the instance to a domain model object for adding a meal planning.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    def to_domain(self) -> CreateMealPlanning:
        """Converts the instance to a domain model object for adding a meal planning."""
        return super().to_domain(CreateMealPlanning)
