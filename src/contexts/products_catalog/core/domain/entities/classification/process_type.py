"""Process type entity for product catalog classification.

Represents a food processing type used for classifying
food products by their processing method.
"""
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.process_type.process_type_created import (
    ProcessTypeCreated,
)


class ProcessType(Classification):
    """Process type entity for food processing classification.
    
    Represents a food processing type used for classifying
    food products by their processing method (e.g., "Raw", "Cooked", "Processed").
    
    Notes:
        Inherits all functionality from Classification base class.
        Emits ProcessTypeCreated event upon creation.
    """
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "ProcessType":
        """Create a new process type classification.
        
        Args:
            name: Process type name (e.g., "Raw", "Cooked", "Processed").
            author_id: User creating the process type.
            description: Optional process type description.
            
        Returns:
            New ProcessType instance with ProcessTypeCreated event.
        """
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=ProcessTypeCreated,
            description=description,
        )
