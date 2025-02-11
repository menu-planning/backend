from src.contexts.products_catalog.shared.domain.entities.classification.base_class import (
    Classification,
)
from src.contexts.products_catalog.shared.domain.events import BrandCreated


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
