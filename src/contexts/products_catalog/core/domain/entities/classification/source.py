from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.source.source_created import (
    SourceCreated,
)


class Source(Classification):
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "Source":
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=SourceCreated,
            description=description,
        )
