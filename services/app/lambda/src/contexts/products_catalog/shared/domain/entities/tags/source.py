from src.contexts.products_catalog.shared.domain.entities.tags.base_tag import Tag
from src.contexts.products_catalog.shared.domain.events import SourceCreated


class Source(Tag):
    @classmethod
    def create_tag(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "Source":
        return super()._create_tag(
            name=name,
            author_id=author_id,
            event_type=SourceCreated,
            description=description,
        )
