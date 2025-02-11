from attrs import frozen
from src.contexts.products_catalog.shared.domain.events.classification.base_class import (
    ClassificationCreated,
)


@frozen
class CategoryCreated(ClassificationCreated):
    pass
