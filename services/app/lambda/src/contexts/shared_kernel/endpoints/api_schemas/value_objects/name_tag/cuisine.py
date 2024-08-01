from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.base_class import (
    ApiNameTag,
)


class ApiCuisine(ApiNameTag):

    @classmethod
    def from_domain(cls, domain_obj: Cuisine) -> "ApiCuisine":
        """Creates an instance of `ApiCuisine` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> Cuisine:
        """Converts the instance to a domain model object."""
        return super().to_domain(Cuisine)
