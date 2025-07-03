from pydantic import Field

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.recipes_catalog.core.domain.meal.commands.rate_recipe import RateRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand


class ApiRateRecipe(BaseApiCommand[RateRecipe]):
    """
    A Pydantic model representing and validating the data required
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

    rating: ApiRating = Field(..., description="Rating to add")

    def to_domain(self) -> RateRecipe:
        """Converts the instance to a domain model object for rating a recipe."""
        try:
            return RateRecipe(rating=self.rating.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiRateRecipe to domain model: {e}")
