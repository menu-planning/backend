from attrs import frozen
from src.contexts.products_catalog.shared.domain.events.tags.base_class import (
    TagCreated,
)


@frozen
class ParentCategoryCreated(TagCreated):
    pass
