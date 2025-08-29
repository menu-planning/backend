from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.classifications.base_classes import (
    CreateClassification,
)


@frozen(kw_only=True)
class CreateBrand(CreateClassification):
    pass
