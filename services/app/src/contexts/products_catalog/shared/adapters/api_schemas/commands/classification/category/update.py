from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.category.update import (
    UpdateCategory,
)


class ApiUpdateCategory(ApiUpdateClassification):

    def to_domain(self) -> UpdateCategory:
        """Converts the instance to a domain model object for updating a Category."""
        return super().to_domain(UpdateCategory)
