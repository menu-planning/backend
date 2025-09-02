"""Source entity for product catalog classification.

Represents a data source used for tracking the origin
and quality of product data in the catalog system.
"""
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.source.source_created import (
    SourceCreated,
)


class Source(Classification):
    """Source entity for data origin tracking.
    
    Represents a data source used for tracking the origin
    and quality of product data (e.g., "USDA", "Manufacturer", "User Input").
    
    Notes:
        Inherits all functionality from Classification base class.
        Emits SourceCreated event upon creation.
    """
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "Source":
        """Create a new source classification.
        
        Args:
            name: Source name (e.g., "USDA", "Manufacturer").
            author_id: User creating the source.
            description: Optional source description.
            
        Returns:
            New Source instance with SourceCreated event.
        """
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=SourceCreated,
            description=description,
        )
