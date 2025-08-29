from typing import Any

from src.contexts.client_onboarding.core.domain.shared.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects import (
    ApiSeedRole,
)


class ApiRole(ApiSeedRole["ApiRole", Role, RoleSaModel]):
    def to_domain(self) -> Role:
        return Role(name=self.name, permissions=frozenset(self.permissions))

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        return cls(name=domain_obj.name, permissions=frozenset(domain_obj.permissions))

    @classmethod
    def from_orm_model(cls, orm_model: RoleSaModel) -> "ApiRole":
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
        return {
            "name": self.name,
            "permissions": (
                ", ".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
