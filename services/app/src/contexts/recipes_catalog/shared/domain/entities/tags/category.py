from __future__ import annotations

from src.contexts.recipes_catalog.shared.domain.entities.tags.base_classes import Tag
from src.contexts.recipes_catalog.shared.domain.events import CategoryCreated
from src.contexts.shared_kernel.domain.enums import Privacy


class Category(Tag):
    @classmethod
    def create_tag(
        cls,
        *,
        name: str,
        author_id: str,
        description: str | None = None,
        privacy: Privacy = Privacy.PRIVATE,
    ) -> "Category":
        return super()._create_tag(
            name=name,
            author_id=author_id,
            event_type=CategoryCreated,
            description=description,
            privacy=privacy,
        )
