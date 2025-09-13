from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.create import (
    CreateFoodGroup,
)


class ApiCreateFoodGroup(ApiCreateClassification):
    """API schema for creating a new food group.

    Inherits from ApiCreateClassification with food group-specific command type.
    """

    command_type = CreateFoodGroup
