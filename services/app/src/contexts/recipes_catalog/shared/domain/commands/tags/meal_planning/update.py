from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    UpdateTag,
)


@frozen(kw_only=True)
class UpdateMealPlanning(UpdateTag):
    pass
