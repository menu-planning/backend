from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)


@frozen(kw_only=True)
class DeleteCategory(DeleteTag):
    pass
