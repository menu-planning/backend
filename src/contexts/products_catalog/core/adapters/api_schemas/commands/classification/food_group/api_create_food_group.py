from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.create import (
    CreateFoodGroup,
)


class ApiCreateFoodGroup(ApiCreateClassification):
    command_type = CreateFoodGroup
