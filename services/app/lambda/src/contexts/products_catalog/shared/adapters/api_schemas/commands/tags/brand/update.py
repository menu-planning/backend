from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.products_catalog.shared.domain.commands.tags.brand.update import (
    UpdateBrand,
)


class ApiUpdateBrand(ApiUpdateTag):

    def to_domain(self) -> UpdateBrand:
        """Converts the instance to a domain model object for updating a Brand."""
        return super().to_domain(UpdateBrand)
