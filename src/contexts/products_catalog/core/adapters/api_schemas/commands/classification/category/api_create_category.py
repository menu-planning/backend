from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.category.create import (
    CreateCategory,
)


class ApiCreateCategory(ApiCreateClassification):
    """API schema for creating a new category.

    Inherits from ApiCreateClassification with category-specific command type.
    """

    command_type = CreateCategory
