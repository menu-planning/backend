from attrs import frozen

from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class BrandCreated(ClassificationCreated):
    pass
