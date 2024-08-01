from src.contexts.products_catalog.shared.domain.entities.tags.base_tag import Tag
from src.contexts.products_catalog.shared.domain.events import ParentCategoryCreated


class ParentCategory(Tag):
    @classmethod
    def create_tag(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "ParentCategory":
        return super()._create_tag(
            name=name,
            author_id=author_id,
            event_type=ParentCategoryCreated,
            description=description,
        )
