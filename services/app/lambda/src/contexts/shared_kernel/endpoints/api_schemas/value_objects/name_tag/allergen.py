from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.base_class import (
    ApiNameTag,
)


class ApiAllergen(ApiNameTag):

    @classmethod
    def from_domain(cls, domain_obj: Allergen) -> "ApiAllergen":
        """Creates an instance of `ApiAllergen` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> Allergen:
        """Converts the instance to a domain model object."""
        return super().to_domain(Allergen)
