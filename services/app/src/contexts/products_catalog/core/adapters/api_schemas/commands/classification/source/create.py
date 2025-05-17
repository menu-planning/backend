from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.base_class import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.core.domain.commands.classifications.source.create import (
    CreateSource,
)


class ApiCreateSource(ApiCreateClassification):
    command_type = CreateSource