from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    CreateTag,
)


@frozen(kw_only=True)
class CreateMealPlanning(CreateTag):
    pass
