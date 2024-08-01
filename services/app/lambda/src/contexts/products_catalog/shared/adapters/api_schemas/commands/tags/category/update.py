from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.products_catalog.shared.domain.commands.tags.category.update import (
    UpdateCategory,
)


class ApiUpdateCategory(ApiUpdateTag):

    def to_domain(self) -> UpdateCategory:
        """Converts the instance to a domain model object for updating a Category."""
        return super().to_domain(UpdateCategory)
