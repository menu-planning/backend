from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.source.update import (
    UpdateSource,
)


class ApiUpdateSource(ApiUpdateClassification):

    def to_domain(self) -> UpdateSource:
        """Converts the instance to a domain model object for updating a Source."""
        return super().to_domain(UpdateSource)
