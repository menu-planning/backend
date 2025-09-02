"""Base event for classification entity creation.

This event is emitted when any classification entity (brand, category,
food group, etc.) is created in the catalog system.
"""
import uuid

from attrs import field, frozen
from src.contexts.seedwork.domain.event import Event


@frozen
class ClassificationCreated(Event):
    """Base event emitted when a classification entity is created.
    
    Attributes:
        name: Name of the classification entity.
        author_id: User who created the classification.
        description: Optional description of the classification.
        classification_id: Unique identifier for the classification (UUID v4 hex).
    
    Notes:
        Emitted by: Classification entity factory methods. Ordering: none.
        Base class for all classification creation events.
    """
    name: str
    author_id: str
    description: str | None = None
    classification_id: str = field(factory=lambda: uuid.uuid4().hex)
