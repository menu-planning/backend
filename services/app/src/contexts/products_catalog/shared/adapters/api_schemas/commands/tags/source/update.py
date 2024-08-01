from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.products_catalog.shared.domain.commands.tags.source.update import (
    UpdateSource,
)


class ApiUpdateSource(ApiUpdateTag):

    def to_domain(self) -> UpdateSource:
        """Converts the instance to a domain model object for updating a Source."""
        return super().to_domain(UpdateSource)
