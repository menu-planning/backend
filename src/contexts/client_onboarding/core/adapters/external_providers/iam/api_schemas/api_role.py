"""
External Provider API Schema: Role

Pydantic model for role data in cross-context communication.
Maps between domain Role objects and ORM models for IAM integration.
"""

from typing import Any

from src.contexts.client_onboarding.core.domain.shared.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_role import (
    ApiSeedRole,
)


class ApiRole(ApiSeedRole["ApiRole", Role, RoleSaModel]):
    """API schema for role data in cross-context communication.

    Extends ApiSeedRole to provide mapping between domain Role objects
    and ORM models for IAM integration in client onboarding context.

    Notes:
        Boundary contract for cross-context communication.
        Handles permission serialization/deserialization for ORM storage.
    """

    def to_domain(self) -> Role:
        """Map API role to domain Role object.

        Returns:
            Role: Domain role object with name and permissions
        """
        return Role(name=self.name, permissions=frozenset(self.permissions))

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Create API role from domain Role object.

        Args:
            domain_obj: Domain Role object

        Returns:
            ApiRole: API role instance
        """
        return cls(name=domain_obj.name, permissions=frozenset(domain_obj.permissions))

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Create API role from ORM model.

        Args:
            orm_model: RoleSaModel ORM instance

        Returns:
            ApiRole: API role instance with parsed permissions
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
        """Convert to ORM model keyword arguments.

        Returns:
            Dictionary with ORM-compatible field values
        """
        return {
            "name": self.name,
            "permissions": (
                ", ".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
