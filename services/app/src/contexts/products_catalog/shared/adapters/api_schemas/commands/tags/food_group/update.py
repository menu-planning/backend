from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.products_catalog.shared.domain.commands.tags.food_group.update import (
    UpdateFoodGroup,
)


class ApiUpdateFoodGroup(ApiUpdateTag):

    def to_domain(self) -> UpdateFoodGroup:
        """Converts the instance to a domain model object for updating a FoodGroup."""
        return super().to_domain(UpdateFoodGroup)
