from attrs import frozen
from src.contexts.products_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)


@frozen(kw_only=True)
class DeleteSource(DeleteTag):
    pass
