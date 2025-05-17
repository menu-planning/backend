from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.update import (
    UpdateFoodGroup,
)


class ApiUpdateFoodGroup(ApiUpdateClassification):
    command_type = UpdateFoodGroup
