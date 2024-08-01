from typing import Any

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.category.update import (
    UpdateCategory,
)


class ApiUpdateCategoryTag(ApiUpdateTag):

    def to_domain(self) -> UpdateCategory:
        """Converts the instance to a domain model object for updating a category."""
        return super().to_domain(UpdateCategory)
