from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.create import (
    CreateParentCategory,
)


class ApiCreateParentCategory(ApiCreateClassification):
    """API schema for creating a new parent category.

    Inherits from ApiCreateClassification with parent category-specific command type.
    """

    command_type = CreateParentCategory
