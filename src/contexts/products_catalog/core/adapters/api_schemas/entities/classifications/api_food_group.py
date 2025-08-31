from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    FoodGroup,
)


class ApiFoodGroup(ApiClassification):
    entity_type = FoodGroup
    entity_type_name = "food_group"
