from attrs import frozen
from src.contexts.products_catalog.shared.domain.commands.tags.base_classes import (
    UpdateTag,
)


@frozen(kw_only=True)
class UpdateFoodGroup(UpdateTag):
    pass
