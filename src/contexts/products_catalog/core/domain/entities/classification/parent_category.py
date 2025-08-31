from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.parent_category.parent_category_created import (
    ParentCategoryCreated,
)


class ParentCategory(Classification):
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "ParentCategory":
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=ParentCategoryCreated,
            description=description,
        )
