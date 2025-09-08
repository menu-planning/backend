from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification.food_group import (
    FoodGroup,
)


class ApiFoodGroup(ApiClassification):
    """API schema for food group entity.

    Inherits from ApiClassification with food group-specific entity type.
    """

    entity_type = FoodGroup
    entity_type_name = "food_group"
