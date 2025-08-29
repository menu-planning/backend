from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.create import (
    CreateParentCategory,
)


class ApiCreateParentCategory(ApiCreateClassification):
    command_type = CreateParentCategory