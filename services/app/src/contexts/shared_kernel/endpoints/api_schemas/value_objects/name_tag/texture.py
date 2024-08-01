from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.base_class import (
    ApiNameTag,
)


class ApiTexture(ApiNameTag):

    @classmethod
    def from_domain(cls, domain_obj: Texture) -> "ApiTexture":
        """Creates an instance of `ApiTexture` from a domain model object."""
        return super().from_domain(domain_obj, cls)

    def to_domain(self) -> Texture:
        """Converts the instance to a domain model object."""
        return super().to_domain(Texture)
