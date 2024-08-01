from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.products_catalog.shared.domain.commands.tags.parent_category.update import (
    UpdateParentCategory,
)


class ApiUpdateParentCategory(ApiUpdateTag):

    def to_domain(self) -> UpdateParentCategory:
        """Converts the instance to a domain model object for updating a ParentCategory."""
        return super().to_domain(UpdateParentCategory)
