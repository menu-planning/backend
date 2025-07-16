from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_classification import (
    ApiClassification,
)
from src.contexts.products_catalog.core.domain.entities.classification import Brand


class ApiBrand(ApiClassification):
    entity_type = Brand
    entity_type_name = "brand"