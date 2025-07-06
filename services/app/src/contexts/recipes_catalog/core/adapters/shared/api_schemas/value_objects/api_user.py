from typing import cast, Dict, Any

from pydantic import Field, field_validator

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_role import ApiRole
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.user import ApiSeedUser


class ApiUser(ApiSeedUser):
    """
    A Pydantic model representing and validating a user in the recipes catalog context.

    This model inherits from ApiSeedUser and overrides the domain type to use the
    recipes catalog specific User value object.
    """

    id: UUIDId
    roles: frozenset[ApiRole] = Field(default_factory=frozenset)

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v: frozenset[ApiRole]) -> frozenset[ApiRole]:
        """Validate that roles are unique and valid."""
        if not v:
            return v
        role_names = [role.name for role in v]
        if len(set(role_names)) != len(role_names):
            raise ValueError("Roles must be unique")
        for role in v:
            if not role.name or not role.name.strip():
                raise ValueError("Role name cannot be empty")
            if not role.permissions:
                raise ValueError("Role must have at least one permission")
            if len(role.permissions) > 50:
                raise ValueError("Role cannot have more than 50 permissions")
        return v

    def to_domain(self) -> User:
        """Converts the instance to a domain model object."""
        seed_user = super().to_domain()
        return User(
            id=seed_user.id,
            roles=set([Role(name=role.name, permissions=role.permissions) for role in self.roles])
        )
    
    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Creates an instance of `ApiUser` from a domain model object."""
        seed_user = User(
            id=domain_obj.id,
            roles=set([Role(name=role.name, permissions=role.permissions) for role in domain_obj.roles])
        )
        base = super().from_domain(seed_user)
        return cast(ApiUser, base)

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Creates an instance of `ApiUser` from an ORM model."""
        roles = []
        if orm_model.roles:
            for role_dict in orm_model.roles:
                if isinstance(role_dict, dict):
                    permissions = role_dict.get('permissions', [])
                    if isinstance(permissions, str):
                        permissions = permissions.split(', ')
                    role = ApiRole(
                        name=role_dict.get('name', ''),
                        permissions=frozenset(permissions)
                    )
                    roles.append(role)
        return cls(
            id=orm_model.id,
            roles=frozenset(roles)
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Converts the instance to ORM model kwargs."""
        return {
            "id": self.id,
            "roles": [{"name": role.name, "permissions": ", ".join(role.permissions)} for role in self.roles] if self.roles else []
        }