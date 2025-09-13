from typing import Self

from pydantic import model_validator
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.base_api_filter import (
    BaseMealApiFilter,
)
from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import (
    MealRepo,
)


class ApiMealFilter(BaseMealApiFilter):
    """
    API filter schema for meal queries with comprehensive filtering capabilities.

    This class extends BaseApiFilter to provide meal-specific filtering options.
    It inherits all common filtering capabilities and adds meal-specific fields.

    Filter Syntax:
    - Single values: "value"
    - Multiple values: "value1|value2|value3" (automatically converted to lists)
    - Tag filters: "key:value1|value2,key2:value3" (parsed into structured format)

    Examples:
        # Filter by multiple IDs
        id: "meal1|meal2|meal3"

        # Filter by multiple authors
        author_id: "user1|user2"

        # Filter by tags with key-value pairs
        tags: "cuisine:italian|mediterranean,meal_type:breakfast|lunch"
        tags_not_exists: "allergen:dairy|nuts"

        # Filter by nutritional ranges
        calories_gte: 200
        calories_lte: 500

        # Filter by time constraints
        total_time_gte: 30
        total_time_lte: 60
    """

    # Meal-specific fields
    menu_id: str | list[str] | None = None
    like: bool | None = None

    @model_validator(mode="after")
    def filter_must_be_allowed_by_repo(self) -> Self:
        return super().validate_repository_filters(MealRepo.filter_to_column_mappers)
