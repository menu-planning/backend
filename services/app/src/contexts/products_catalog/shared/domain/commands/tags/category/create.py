from attrs import frozen
from src.contexts.products_catalog.shared.domain.commands.tags.base_classes import (
    CreateTag,
)


@frozen(kw_only=True)
class CreateCategory(CreateTag):
    pass
