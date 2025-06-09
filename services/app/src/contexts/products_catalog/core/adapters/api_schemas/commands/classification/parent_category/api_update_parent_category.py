from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.update import (
    UpdateParentCategory,
)


class ApiUpdateParentCategory(ApiUpdateClassification):
    command_type = UpdateParentCategory