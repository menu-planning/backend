from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import SanitizedText, UUIDId
from pydantic import Field, TypeAdapter


class ApiTag(BaseApiValueObject[Tag, TagSaModel]):
    """A class to represent and validate a tag with security-enhanced input validation."""

    key: SanitizedText = Field(..., min_length=1, max_length=100)
    value: SanitizedText = Field(..., min_length=1, max_length=200)
    author_id: UUIDId = Field(..., description="User ID who created this tag")
    type: SanitizedText = Field(..., min_length=1, max_length=50)

    @classmethod
    def from_domain(cls, domain_obj: Tag) -> "ApiTag":
        """Creates an instance of `ApiTag` from a domain model object."""
        return cls(
            key=domain_obj.key,
            value=domain_obj.value,
            author_id=domain_obj.author_id,
            type=domain_obj.type,
        )

    def to_domain(self) -> Tag:
        """Converts the instance to a domain model object."""
        return Tag(
            key=self.key,
            value=self.value,
            author_id=self.author_id,
            type=self.type,
        )

    @classmethod
    def from_orm_model(cls, orm_model: TagSaModel) -> "ApiTag":
        """Convert from ORM model."""
        return cls.model_validate(orm_model)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return self.model_dump()