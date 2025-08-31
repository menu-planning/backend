from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.category.create import (
    CreateCategory,
)


class ApiCreateCategory(ApiCreateClassification):
    command_type = CreateCategory
