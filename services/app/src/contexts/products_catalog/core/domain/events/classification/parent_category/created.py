from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.base_class import (
    ClassificationCreated,
)


@frozen
class ParentCategoryCreated(ClassificationCreated):
    pass
