from pydantic import BaseModel
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class ApiTag(BaseModel, frozen=True):
    key: str
    value: str
    author_id: str
    type: str

    @classmethod
    def from_domain(cls, domain_obj: Tag) -> "ApiTag":
        try:
            return cls(
                key=domain_obj.key,
                value=domain_obj.value,
                author_id=domain_obj.author_id,
                type=domain_obj.type,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiTag from domain instance: {e}")

    def to_domain(self) -> Tag:
        try:
            return Tag(
                key=self.key,
                value=self.value,
                author_id=self.author_id,
                type=self.type,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
