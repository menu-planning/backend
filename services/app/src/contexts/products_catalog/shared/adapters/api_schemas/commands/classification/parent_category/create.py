from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.base_class import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.parent_category.create import (
    CreateParentCategory,
)


class ApiCreateParentCategory(ApiCreateClassification):
    """A Pydantic model representing and validating the the data required
    to add a new parent category via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the parent category.
        author (ApiUser): The user adding the parent category.
        description (str, optional): Detailed description of the parent category.

    Methods:
        to_domain() -> CreateParentCategory:
            Converts the instance to a domain model object for adding a parent category.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    def to_domain(self) -> CreateParentCategory:
        """Converts the instance to a domain model object for adding a parent category."""
        return super().to_domain(CreateParentCategory)
