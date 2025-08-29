from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.products_catalog.core.domain.events.classification.process_type.process_type_created import ProcessTypeCreated


class ProcessType(Classification):
    @classmethod
    def create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
    ) -> "ProcessType":
        return super()._create_classification(
            name=name,
            author_id=author_id,
            event_type=ProcessTypeCreated,
            description=description,
        )
