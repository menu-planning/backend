from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.update import (
    ApiUpdateTag,
)
from src.contexts.products_catalog.shared.domain.commands.tags.process_type.update import (
    UpdateProcessType,
)


class ApiUpdateProcessType(ApiUpdateTag):

    def to_domain(self) -> UpdateProcessType:
        """Converts the instance to a domain model object for updating a ProcessType."""
        return super().to_domain(UpdateProcessType)
