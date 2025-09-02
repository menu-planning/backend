from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.update import (
    UpdateFoodGroup,
)


class ApiUpdateFoodGroup(ApiUpdateClassification):
    """API schema for updating a food group.
    
    Inherits from ApiUpdateClassification with food group-specific command type.
    """
    command_type = UpdateFoodGroup
