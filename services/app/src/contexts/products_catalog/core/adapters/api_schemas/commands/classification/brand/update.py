from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.brand.update import (
    UpdateBrand,
)


class ApiUpdateBrand(ApiUpdateClassification):
    command_type = UpdateBrand
