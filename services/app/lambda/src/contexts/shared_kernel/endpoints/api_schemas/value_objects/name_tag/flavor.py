from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.base_class import (
    ApiNameTag,
)


class ApiFlavor(ApiNameTag):

    @classmethod
    def from_domain(cls, domain_obj: Flavor) -> "ApiFlavor":
        """Creates an instance of `ApiFlavor` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> Flavor:
        """Converts the instance to a domain model object."""
        return super().to_domain(Flavor)
