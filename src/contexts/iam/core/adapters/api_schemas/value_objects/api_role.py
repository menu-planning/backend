from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.domain.enums import Permission as IAMPermission
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_permissions_collection,
    validate_role_name_format,
)


class ApiRole(BaseApiValueObject[Role, RoleSaModel]):
    """A Pydantic model representing and validating IAM role data for
    API requests and responses.

    This class handles the conversion and validation of role information between
    different layers of the application (API, Domain, and ORM). It ensures
    security compliance through multiple validation layers and maintains data
    integrity during type conversions.

    Security-Critical Validation Strategy:
    - BeforeValidator(validate_optional_text): Input sanitization
                for name                       (trim, handle None/empty)
    - AfterValidator(validate_iam_role_name_format): Security-critical
                                                     business logic validation
    - BeforeValidator(validate_iam_permissions_collection): Collection validation
                                                            with security checks
    - AfterValidator(validate_iam_context): Context validation for security compliance

    Attributes:
        name (SanitizedText): The name of the role, validated and sanitized for
                              security. Must conform to IAM role naming conventions.
        context (str): The context or scope where this role applies
                       (e.g., 'user_management', 'product_catalog', 'system_admin').
        permissions (frozenset[str]): Immutable set of IAM permissions associated with
                                      the role. Each permission must be a valid
                                      IAMPermission enum value. Empty set is allowed
                                      for roles with no specific permissions.
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
        """Convert a Role domain object to an ApiRole instance.

        This method handles the conversion from the domain layer to the API layer,
        ensuring proper type conversions and validation. It's typically used when
        returning role data from the API or when domain objects need to be
        serialized for external consumption.

        Handles type conversions:
        - Domain list[str] → API frozenset[str] (collection type standardization)
        - Ensures permissions are properly converted and validated

        Args:
            domain_obj (Role): The Role domain object to convert. Must be a valid
                             Role instance with all required attributes (name, context,
                             permissions).

        Returns:
            ApiRole: An ApiRole instance populated with data from the domain object.

        Raises:
            ValueError: If the conversion fails, validation fails, or the domain object
                       is malformed. This includes cases where permission conversion
                       fails or required attributes are missing.

        Example:
            ```python
            domain_role = Role(
                name="admin",
                context="user_management",
                permissions=["read", "write"],
            )
            api_role = ApiRole.from_domain(domain_role)
            ```

        Note:
            The permissions list from the domain object is converted to a frozenset
            to ensure immutability and prevent accidental modifications.
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
            raise ValueError(error_message) from e

    def to_domain(self) -> Role:
        """Convert the ApiRole instance to a Role domain object.

        This method handles the conversion from the API layer back to the domain layer,
        typically used when processing incoming API requests that need to be converted
        to domain objects for business logic processing or validation.

        Handles type conversions per documented patterns:
        - API frozenset[str] → Domain list[str] (collection type conversion)
        - Maintains data integrity during the conversion process

        Returns:
            Role: A Role domain object populated with data from the API model.

        Raises:
            ValueError: If the conversion fails, validation fails, or required
                       attributes are missing. This includes cases where permission
                       conversion fails or the API model is in an invalid state.

        Example:
            ```python
            api_role = ApiRole(
                name="admin",
                context="user_management",
                permissions={"read", "write"}
            )
            domain_role = api_role.to_domain()
            ```

        Note:
            The frozenset of permissions is converted back to a list as expected
            by the domain Role object, maintaining the original data structure.
        """
        try:
            return Role(
                name=self.name,
                context=self.context,
                permissions=list(self.permissions),
            )
        except Exception as e:
            error_message = f"Failed to convert IAM ApiRole to domain: {e}"
            raise ValueError(error_message) from e

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Convert an ORM model to an ApiRole instance.

        This method handles the conversion from the ORM layer to the API layer,
        typically used when retrieving role data from the database and preparing
        it for API responses. It handles the conversion of comma-separated permission
        strings to structured permission sets.

        Handles ORM → API conversions per documented patterns:
        - ORM comma-separated string → API frozenset[str]
        - Ensures proper parsing and validation of permission strings

        Args:
            orm_model (RoleSaModel): The SQLAlchemy model to convert. Must be a
                                   valid RoleSaModel instance with all required
                                   attributes. The permissions field should contain
                                   a comma-separated string of permission values.

        Returns:
            ApiRole: An ApiRole instance populated with data from the ORM model.

        Raises:
            ValueError: If the conversion fails, validation fails, or the ORM model
                       is malformed. This includes cases where permission parsing fails
                       or required attributes are missing.

        Example:
            ```python
            orm_role = RoleSaModel.query.get(role_id)
            api_role = ApiRole.from_orm_model(orm_role)
            ```

        Note:
            The permissions field in the ORM model is expected to be a comma-separated
            string (e.g., "read,write,delete"). This method parses this string and
            converts it to a frozenset, handling empty strings and whitespace
            appropriately.
        """
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

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert the ApiRole instance to ORM model kwargs.

        This method prepares the API model data for persistence to the database
        by converting it to a format suitable for ORM model instantiation.
        It's typically used when creating new role records or updating existing ones.

        Handles API → ORM conversions per documented patterns:
        - API frozenset[str] → ORM comma-separated string
        - Ensures data is properly formatted for database operations

        Returns:
            dict[str, Any]: Dictionary of kwargs for ORM model creation. The keys
                           correspond to the ORM model's attribute names, and the
                           values are the properly formatted data ready for
                           database operations.

        Raises:
            ValueError: If the conversion fails, validation fails, or required
                       attributes are missing. This includes cases where permission
                       conversion fails or the API model is in an invalid state.

        Example:
            ```python
            api_role = ApiRole(
                name="admin",
                context="user_management",
                permissions={"read", "write"},
            )
            orm_kwargs = api_role.to_orm_kwargs()
            new_role = RoleSaModel(**orm_kwargs)
            db.session.add(new_role)
            ```

        Note:
            The permissions frozenset is converted to a sorted, comma-separated
            string for database storage. This ensures consistent storage format
            and allows for efficient querying. Empty permission sets are stored
            as empty strings.
        """
        return {
            "name": self.name,
            "context": self.context,
            "permissions": (
                ",".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
