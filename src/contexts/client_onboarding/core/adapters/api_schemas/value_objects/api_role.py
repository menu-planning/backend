from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field
from src.contexts.client_onboarding.core.domain.enums import (
    Permission as RecipesPermission,
)
from src.contexts.client_onboarding.core.domain.shared.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_permissions_collection,
    validate_role_name_format,
)
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_role import (
    ApiSeedRole,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiRole(ApiSeedRole):
    """A class to represent and validate a role in the IAM context.

    Security-Critical Validation Strategy:
    - BeforeValidator(validate_optional_text): Input sanitization
        (trim, handle None/empty)
    - AfterValidator(validate_iam_role_name_format): Security-critical business logic
        validation
    - BeforeValidator(validate_iam_permissions_collection): Collection validation with
    security checks
    - AfterValidator(validate_iam_context): Context validation for security compliance
    """

    name: Annotated[SanitizedText, AfterValidator(validate_role_name_format)]
    permissions: Annotated[
        frozenset[str],
        BeforeValidator(
            lambda v: validate_permissions_collection(
                v, allowed_permissions={perm.value for perm in RecipesPermission}
            )
        ),
        Field(
            default_factory=frozenset,
            description="Set of IAM permissions associated with the role",
        ),
    ]

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Convert a Role domain object to an ApiRole instance.

        Handles type conversions:
        - Domain list[str] → API frozenset[str] (collection type standardization)

        Args:
            domain_obj: The Role domain object to convert

        Returns:
            An ApiRole instance

        Raises:
            ValidationConversionError: If conversion fails or security validation fails
        """
        try:
            return cls(
                name=domain_obj.name,
                permissions=frozenset(
                    domain_obj.permissions
                ),  # list → frozenset conversion
            )
        except Exception as e:
            error_msg = f"Failed to build IAM ApiRole from domain: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=cls,
                conversion_direction="domain_to_api",
                source_data={"domain_obj": str(domain_obj)},
                validation_errors=[str(e)],
            ) from e

    def to_domain(self) -> Role:
        """Convert the ApiRole instance to a Role domain object.

        Handles type conversions per documented patterns:
        - API frozenset[str] → Domain list[str] (collection type conversion)

        Returns:
            A Role domain object

        Raises:
            ValidationConversionError: If conversion fails
        """
        try:
            return Role(
                name=self.name,
                permissions=frozenset(self.permissions),  # frozenset → set conversion
            )
        except Exception as e:
            error_msg = f"Failed to convert IAM ApiRole to domain: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Convert an ORM model to an ApiRole instance.

        Handles ORM → API conversions per documented patterns:
        - ORM comma-separated string → API frozenset[str]

        Args:
            orm_model: The SQLAlchemy model to convert

        Returns:
            An ApiRole instance
        """
        return cls(
            name=orm_model.name,
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

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert the ApiRole instance to ORM model kwargs.

        Handles API → ORM conversions per documented patterns:
        - API frozenset[str] → ORM comma-separated string

        Returns:
            Dictionary of kwargs for ORM model creation
        """
        return {
            "name": self.name,
            "permissions": (
                ",".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
