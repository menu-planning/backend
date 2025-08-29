from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.category.update import (
    UpdateCategory,
)


class ApiUpdateCategory(ApiUpdateClassification):
    command_type = UpdateCategory
