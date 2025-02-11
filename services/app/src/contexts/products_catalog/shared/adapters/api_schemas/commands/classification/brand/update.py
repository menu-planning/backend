from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.brand.update import (
    UpdateBrand,
)


class ApiUpdateBrand(ApiUpdateClassification):

    def to_domain(self) -> UpdateBrand:
        """Converts the instance to a domain model object for updating a Brand."""
        return super().to_domain(UpdateBrand)
