from attrs import frozen
from src.contexts.products_catalog.shared.domain.commands.classifications.base_classes import (
    UpdateClassification,
)


@frozen(kw_only=True)
class UpdateFoodGroup(UpdateClassification):
    pass
