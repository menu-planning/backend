"""API value object for tags with validation and conversions."""

from pydantic import Field
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class ApiTag(BaseApiValueObject[Tag, TagSaModel]):
    """API schema for tag operations.

    Attributes:
        key: Tag key identifier, length 1-100 characters.
        value: Tag value content, length 1-200 characters.
        author_id: UUID of user who created this tag.
        type: Tag type identifier, length 1-50 characters.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        All string fields are sanitized and trimmed automatically.
    """

    key: SanitizedText = Field(..., min_length=1, max_length=100)
    value: SanitizedText = Field(..., min_length=1, max_length=200)
    author_id: UUIDIdRequired = Field(..., description="User ID who created this tag")
    type: SanitizedText = Field(..., min_length=1, max_length=50)

    @classmethod
    def from_domain(cls, domain_obj: Tag) -> "ApiTag":
        """Create an instance from a domain model.

        Args:
            domain_obj: Source domain model.

        Returns:
            ApiTag instance.
        """
        return cls(
            key=domain_obj.key,
            value=domain_obj.value,
            author_id=domain_obj.author_id,
            type=domain_obj.type,
        )

    def to_domain(self) -> Tag:
        """Convert this value object into a domain model.

        Returns:
            Tag domain model.
        """
        return Tag(
            key=self.key,
            value=self.value,
            author_id=self.author_id,
            type=self.type,
        )

    @classmethod
    def from_orm_model(cls, orm_model: TagSaModel) -> "ApiTag":
        """Create an instance from an ORM model.

        Args:
            orm_model: ORM instance representing a tag.

        Returns:
            ApiTag instance.
        """
        return cls.model_validate(orm_model)

    def to_orm_kwargs(self) -> dict:
        """Return kwargs suitable for constructing/updating an ORM model.

        Returns:
            Mapping of ORM field names to values.
        """
        return self.model_dump()
