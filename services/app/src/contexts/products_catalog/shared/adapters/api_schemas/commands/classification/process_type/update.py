from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.update import (
    ApiUpdateClassification,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.process_type.update import (
    UpdateProcessType,
)


class ApiUpdateProcessType(ApiUpdateClassification):

    def to_domain(self) -> UpdateProcessType:
        """Converts the instance to a domain model object for updating a ProcessType."""
        return super().to_domain(UpdateProcessType)
