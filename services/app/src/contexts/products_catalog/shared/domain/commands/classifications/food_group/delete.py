from attrs import frozen
from src.contexts.products_catalog.shared.domain.commands.classifications.base_classes import (
    DeleteClassification,
)


@frozen(kw_only=True)
class DeleteFoodGroup(DeleteClassification):
    pass
