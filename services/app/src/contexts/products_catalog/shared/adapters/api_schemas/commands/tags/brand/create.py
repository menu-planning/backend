from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.base_class import (
    ApiCreateTag,
)
from src.contexts.products_catalog.shared.domain.commands import CreateBrand


class ApiCreateBrand(ApiCreateTag):
    """A Pydantic model representing and validating the the data required
    to add a new brand via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the brand.
        author (ApiUser): The user adding the brand.
        description (str, optional): Detailed description of the brand.

    Methods:
        to_domain() -> CreateBrand:
            Converts the instance to a domain model object for adding a brand.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    def to_domain(self) -> CreateBrand:
        """Converts the instance to a domain model object for adding a brand."""
        return super().to_domain(CreateBrand)
