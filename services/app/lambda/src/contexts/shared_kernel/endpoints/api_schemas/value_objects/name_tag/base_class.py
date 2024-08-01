from pydantic import BaseModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.base_class import NameTag


class ApiNameTag(BaseModel):
    name: str

    @classmethod
    def from_domain(
        cls, domain_obj: NameTag, entity_type: type[NameTag]
    ) -> "ApiNameTag":
        try:
            return entity_type(
                name=domain_obj.name,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiNameTag from domain instance: {e}")

    def to_domain(self, entity_type: type[NameTag]) -> NameTag:
        try:
            return entity_type(
                name=self.name,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
