"""Event emitted when a process type classification is created.

This event is triggered when a new process type entity is created
in the product catalog system.
"""
from attrs import frozen
from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)


@frozen
class ProcessTypeCreated(ClassificationCreated):
    """Event emitted when a process type classification is created.
    
    Attributes:
        name: Process type name.
        author_id: User who created the process type.
        description: Optional process type description.
        classification_id: Unique identifier for the process type.
    
    Notes:
        Emitted by: ProcessType.create_classification(). Ordering: none.
        Inherits all attributes from ClassificationCreated.
    """
    pass
