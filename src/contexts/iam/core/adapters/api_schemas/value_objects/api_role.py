from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.domain.enums import Permission as IAMPermission
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_permissions_collection,
    validate_role_name_format,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiRole(BaseApiValueObject[Role, RoleSaModel]):
    """API schema for IAM role value object.

    Attributes:
        name: Role name, validated and sanitized for security.
        context: Context or scope where this role applies.
        permissions: Immutable set of IAM permissions associated with the role.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
    """

    name: Annotated[SanitizedText, AfterValidator(validate_role_name_format)]
    context: Annotated[str, Field(..., description="The context of the role")]
    permissions: Annotated[
        frozenset[str],
        BeforeValidator(
            lambda v: validate_permissions_collection(
                v, allowed_permissions={perm.value for perm in IAMPermission}
            )
        ),
        Field(
            default_factory=frozenset,
            description="Set of IAM permissions associated with the role",
        ),
    ]

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Map domain role to API role.

        Args:
            domain_obj: Domain role object to convert.

        Returns:
            API role instance populated with data from domain object.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return cls(
                name=domain_obj.name,
                context=domain_obj.context,
                permissions=frozenset(
                    domain_obj.permissions
                ),  # list → frozenset conversion
            )
        except Exception as e:
            error_message = f"Failed to build IAM ApiRole from domain: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=cls,
                conversion_direction="domain_to_api",
                source_data=domain_obj,
                validation_errors=[str(e)],
            ) from e

    def to_domain(self) -> Role:
        """Map API role to domain role.

        Returns:
            Domain role object populated with data from API model.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return Role(
                name=self.name,
                context=self.context,
                permissions=list(self.permissions),
            )
        except Exception as e:
            error_message = f"Failed to convert IAM ApiRole to domain: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self,
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Map ORM role model to API role.

        Args:
            orm_model: SQLAlchemy role model to convert.

        Returns:
            API role instance populated with data from ORM model.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return cls(
                name=orm_model.name,
                context=orm_model.context,
                permissions=(
                    frozenset(
                        perm.strip()
                        for perm in orm_model.permissions.split(",")
                        if perm.strip()
                    )
                    if orm_model.permissions
                    else frozenset()
                ),
            )
        except Exception as e:
            error_message = f"Failed to build IAM ApiRole from ORM model: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=cls,
                conversion_direction="orm_to_api",
                source_data=orm_model,
                validation_errors=[str(e)],
            ) from e

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Map API role to ORM model kwargs.

        Returns:
            Dictionary of kwargs for ORM model creation.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.

        Notes:
            Lossless: Yes. Timezone: UTC assumption.
        """
        try:
            return {
                "name": self.name,
                "context": self.context,
                "permissions": (
                    ",".join(sorted(self.permissions)) if self.permissions else ""
                ),
            }
        except Exception as e:
            error_message = f"Failed to convert IAM ApiRole to ORM kwargs: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_orm",
                source_data=self,
                validation_errors=[str(e)],
            ) from e
