from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.brand.update import (
    UpdateBrand,
)


class ApiUpdateBrand(ApiUpdateClassification):
    """API schema for updating a brand.

    Inherits from ApiUpdateClassification with brand-specific command type.
    """

    command_type = UpdateBrand
