from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.base_class import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.brand.create import (
    CreateBrand,
)


class ApiCreateBrand(ApiCreateClassification):
    command_type = CreateBrand