from typing import Any

from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_role import (
    ApiSeedRole,
)


class ApiRole(ApiSeedRole["ApiRole", Role, RoleSaModel]):
    """IAM provider specific role model for recipes catalog context.

    Extends ApiSeedRole for cross-context role data exchange between IAM
    and recipes catalog. Handles permission serialization/deserialization
    and ORM model conversion.

    Attributes:
        Inherits all fields from ApiSeedRole including name and permissions.

    Notes:
        Boundary contract for IAM role data in recipes catalog context.
        Maintains compatibility with base role schema patterns.
    """

    def to_domain(self) -> Role:
        """Convert API schema instance to domain model object.

        Returns:
            Role domain object with permissions converted to frozenset.

        Notes:
            Converts permissions list to frozenset for domain model.
        """
        return Role(name=self.name, permissions=frozenset(self.permissions))

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Create API schema instance from domain model object.

        Args:
            domain_obj: Role domain object to convert.

        Returns:
            ApiRole instance populated from domain object.

        Notes:
            Converts domain permissions frozenset to list for API schema.
        """
        return cls(name=domain_obj.name, permissions=frozenset(domain_obj.permissions))

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Create API schema instance from ORM model.

        Args:
            orm_model: RoleSaModel ORM instance to convert.

        Returns:
            ApiRole instance populated from ORM model.

        Notes:
            Handles comma-separated string permissions from ORM.
            Strips whitespace and filters empty permissions.
        """
        return cls(
            name=orm_model.name,
            permissions=(
                frozenset(
                    perm.strip()
                    for perm in orm_model.permissions.split(", ")
                    if perm.strip()
                )
                if orm_model.permissions
                else frozenset()
            ),
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema instance to ORM model kwargs.

        Returns:
            Dictionary of kwargs for ORM model creation.

        Notes:
            Converts permissions frozenset to comma-separated string.
            Sorts permissions for consistent storage.
        """
        return {
            "name": self.name,
            "permissions": (
                ", ".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
