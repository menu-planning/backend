from typing import Any

from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.products_catalog.core.domain.value_objects.role import Role
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_role import (
    ApiSeedRole,
)


class ApiRole(ApiSeedRole["ApiRole", Role, RoleSaModel]):
    """API schema for Role entity in products catalog context.

    Extends ApiSeedRole with products catalog specific role handling.
    """

    def to_domain(self) -> Role:
        """Convert API role to domain role.

        Returns:
            Role domain object.
        """
        return Role(name=self.name, permissions=frozenset(self.permissions))

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        """Create API role from domain role.

        Args:
            domain_obj: Role domain object.

        Returns:
            ApiRole instance.
        """
        return cls(name=domain_obj.name, permissions=frozenset(domain_obj.permissions))

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
        """Create API role from SQLAlchemy model.

        Args:
            orm_model: RoleSaModel instance.

        Returns:
            ApiRole instance.
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
        """Convert API role to ORM model kwargs.

        Returns:
            Dictionary of ORM model attributes.
        """
        return {
            "name": self.name,
            "permissions": (
                ", ".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
