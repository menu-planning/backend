from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_create_classification import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.brand.create import (
    CreateBrand,
)


class ApiCreateBrand(ApiCreateClassification):
    """API schema for creating a new brand.

    Inherits from ApiCreateClassification with brand-specific command type.
    """

    command_type = CreateBrand
