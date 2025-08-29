from typing import Any

from pydantic import model_validator

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.base_api_filter import (  # noqa: E501
    BaseMealApiFilter,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs import (
    AverageRatingValue,
)
from src.contexts.recipes_catalog.core.adapters.meal.repositories import (
    RecipeRepo,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiModel,
)


class ApiRecipeFilter(BaseMealApiFilter, BaseApiModel[Any, Any]):
    """
    API filter schema for recipe queries with comprehensive filtering capabilities.

    This class extends BaseApiFilter to provide recipe-specific filtering options.
    It inherits all common filtering capabilities and adds recipe-specific fields.

    Filter Syntax:
    - Single values: "value"
    - Multiple values: "value1|value2|value3" (automatically converted to lists)
    - Tag filters: "key:value1|value2,key2:value3" (parsed into structured format)

    Examples:
        # Filter by multiple IDs
        id: "recipe1|recipe2|recipe3"

        # Filter by multiple authors
        author_id: "user1|user2"

        # Filter by tags with key-value pairs
        tags: "cuisine:italian|mediterranean,meal_type:breakfast|lunch"
        tags_not_exists: "allergen:dairy|nuts"

        # Filter by nutritional ranges
        calories_gte: 200.5
        calories_lte: 500.0

        # Filter by time constraints
        total_time_gte: 30
        total_time_lte: 60

        # Filter by ratings
        average_taste_rating_gte: 4.0
        average_convenience_rating_gte: 3.5
    """

    # Recipe-specific fields
    meal_id: str | list[str] | None = None

    # Rating filters
    average_taste_rating_gte: AverageRatingValue | None = None
    average_convenience_rating_gte: AverageRatingValue | None = None

    @model_validator(mode="before")
    @classmethod
    def filter_must_be_allowed_by_repo(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Validates that only allowed filters are used.

        This validator ensures that all provided filter keys are supported
        by the underlying repository layer, preventing invalid filter errors.

        Args:
            values: The filter values to validate

        Returns:
            dict: The validated filter values

        Raises:
            ValueError: If an invalid filter key is provided
        """
        # Use the base class validation method
        instance = cls()
        return instance.validate_repository_filters(
            values, RecipeRepo.filter_to_column_mappers
        )
