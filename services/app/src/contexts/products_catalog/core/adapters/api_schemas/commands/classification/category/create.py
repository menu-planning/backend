from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.base_class import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.category.create import (
    CreateCategory,
)


class ApiCreateCategory(ApiCreateClassification):
    command_type = CreateCategory