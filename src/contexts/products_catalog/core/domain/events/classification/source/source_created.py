"""Event emitted when a source classification is created.

This event is triggered when a new source entity is created
in the product catalog system.
"""
from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class SourceCreated(ClassificationCreated):
    """Event emitted when a source classification is created.
    
    Attributes:
        name: Source name.
        author_id: User who created the source.
        description: Optional source description.
        classification_id: Unique identifier for the source.
    
    Notes:
        Emitted by: Source.create_classification(). Ordering: none.
        Inherits all attributes from ClassificationCreated.
    """
    pass
