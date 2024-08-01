from typing import Any

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.meal_planning.update import (
    UpdateMealPlanning,
)


class ApiUpdateMealPlanningTag(ApiUpdateTag):

    def to_domain(self) -> UpdateMealPlanning:
        """Converts the instance to a domain model object for updating a MealPlanning."""
        return super().to_domain(UpdateMealPlanning)
