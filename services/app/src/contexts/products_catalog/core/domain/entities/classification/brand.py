from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.brand.brand_created import BrandCreated


class Brand(Classification):
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "Brand":
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=BrandCreated,
            description=description,
        )
