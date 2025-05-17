from pydantic import BaseModel
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.rating import (
    ApiRating,
)
from src.contexts.recipes_catalog.core.domain.commands import RateRecipe


class ApiRateRecipe(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to rate a recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        rating (Rating): Rating to add.

    Methods:
        to_domain() -> RateRecipe:
            Converts the instance to a domain model object for rating a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    rating: ApiRating

    def to_domain(self) -> RateRecipe:
        """Converts the instance to a domain model object for rating a recipe."""
        try:
            return RateRecipe(rating=self.rating.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiRateRecipeto domain model: {e}")
