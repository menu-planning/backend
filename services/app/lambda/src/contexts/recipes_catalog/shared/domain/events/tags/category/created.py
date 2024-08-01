from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.events.tags.base_created import (
    TagCreated,
)


@frozen
class CategoryCreated(TagCreated):
    pass
