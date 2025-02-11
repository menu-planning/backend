from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.food_group.update import (
    UpdateFoodGroup,
)


class ApiUpdateFoodGroup(ApiUpdateClassification):

    def to_domain(self) -> UpdateFoodGroup:
        """Converts the instance to a domain model object for updating a FoodGroup."""
        return super().to_domain(UpdateFoodGroup)
