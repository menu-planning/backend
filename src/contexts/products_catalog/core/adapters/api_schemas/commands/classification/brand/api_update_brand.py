from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.api_update_classification import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.brand.update import (
    UpdateBrand,
)


class ApiUpdateBrand(ApiUpdateClassification):
    command_type = UpdateBrand
