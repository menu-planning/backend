"""Brand entity for product catalog classification.

Represents a brand/manufacturer that can be associated with products
in the catalog system.
"""
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.brand.brand_created import (
    BrandCreated,
)


class Brand(Classification):
    """Brand entity for product classification.
    
    Represents a brand or manufacturer that can be associated with products.
    Used for organizing and filtering products by their brand identity.
    
    Notes:
        Inherits all functionality from Classification base class.
        Emits BrandCreated event upon creation.
    """
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "Brand":
        """Create a new brand classification.
        
        Args:
            name: Brand name (e.g., "Nike", "Apple").
            author_id: User creating the brand.
            description: Optional brand description.
            
        Returns:
            New Brand instance with BrandCreated event.
        """
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=BrandCreated,
            description=description,
        )
