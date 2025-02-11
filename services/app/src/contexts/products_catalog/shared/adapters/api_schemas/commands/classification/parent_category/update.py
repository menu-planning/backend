from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.parent_category.update import (
    UpdateParentCategory,
)


class ApiUpdateParentCategory(ApiUpdateClassification):

    def to_domain(self) -> UpdateParentCategory:
        """Converts the instance to a domain model object for updating a ParentCategory."""
        return super().to_domain(UpdateParentCategory)
