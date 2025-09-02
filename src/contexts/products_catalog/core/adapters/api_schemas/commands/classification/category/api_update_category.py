from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.category.update import (
    UpdateCategory,
)


class ApiUpdateCategory(ApiUpdateClassification):
    """API schema for updating a category.
    
    Inherits from ApiUpdateClassification with category-specific command type.
    """
    command_type = UpdateCategory
