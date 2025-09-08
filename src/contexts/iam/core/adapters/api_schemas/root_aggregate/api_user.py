from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import Field
from src.contexts.iam.core.adapters.api_schemas.value_objects.api_role import ApiRole
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiEntity,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiUser(BaseApiEntity[User, UserSaModel]):
    """API schema for user aggregate.

    Attributes:
        roles: Frozenset of IAM roles assigned to the user.
        discarded: Whether the user is discarded/deleted.
        version: Version number for optimistic locking during concurrent updates.
        created_at: Timestamp when the user was created.
        updated_at: Timestamp when the user was last updated.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
    """

    roles: Annotated[
        frozenset[ApiRole],
        Field(
            default_factory=frozenset,
            description="Set of IAM roles assigned to the user",
        ),
    ]

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Map domain user to API user.

        Args:
            domain_obj: Domain user object to convert.

        Returns:
            API user instance populated with data from domain object.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return cls(
                id=domain_obj.id,
                roles=(
                    frozenset([ApiRole.from_domain(role) for role in domain_obj.roles])
                    if domain_obj.roles
                    else frozenset()
                ),  # list → frozenset conversion
                discarded=domain_obj.discarded,
                version=domain_obj.version,
                created_at=domain_obj.created_at or datetime.now(UTC),
                updated_at=domain_obj.updated_at or datetime.now(UTC),
            )
        except Exception as e:
            error_message = f"Failed to build IAM ApiUser from domain: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=cls,
                conversion_direction="domain_to_api",
                source_data=domain_obj,
                validation_errors=[str(e)],
            ) from e

    def to_domain(self) -> User:
        """Map API user to domain user.

        Returns:
            Domain user object populated with data from API model.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return User(
                id=str(self.id),
                roles=(
                    [role.to_domain() for role in self.roles] if self.roles else []
                ),  # frozenset → list conversion
                discarded=self.discarded,
                version=self.version,
                created_at=self.created_at,
                updated_at=self.updated_at,
            )
        except Exception as e:
            error_message = f"Failed to convert IAM ApiUser to domain: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self,
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Map ORM user model to API user.

        Args:
            orm_model: SQLAlchemy user model to convert.

        Returns:
            API user instance populated with data from ORM model.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return cls(
                id=orm_model.id,
                roles=(
                    frozenset(
                        [ApiRole.from_orm_model(role) for role in orm_model.roles]
                    )
                    if orm_model.roles
                    else frozenset()
                ),
                discarded=orm_model.discarded,
                version=orm_model.version,
                created_at=orm_model.created_at or datetime.now(UTC),
                updated_at=orm_model.updated_at or datetime.now(UTC),
            )
        except Exception as e:
            error_message = f"Failed to build IAM ApiUser from ORM model: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=cls,
                conversion_direction="orm_to_api",
                source_data=orm_model,
                validation_errors=[str(e)],
            ) from e

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Map API user to ORM model kwargs.

        Returns:
            Dictionary of kwargs for ORM model creation.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return {
                "id": str(self.id),
                "roles": (
                    [role.to_orm_kwargs() for role in self.roles] if self.roles else []
                ),
                "discarded": self.discarded,
                "version": self.version,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        except Exception as e:
            error_message = f"Failed to convert IAM ApiUser to ORM kwargs: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_orm",
                source_data=self,
                validation_errors=[str(e)],
            ) from e
