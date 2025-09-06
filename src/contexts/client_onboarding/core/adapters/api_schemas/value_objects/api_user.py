from typing import Annotated

from pydantic import Field
from src.contexts.client_onboarding.core.adapters.api_schemas.value_objects.api_role import (
    ApiRole,
)
from src.contexts.client_onboarding.core.domain.shared.value_objects.role import Role
from src.contexts.client_onboarding.core.domain.shared.value_objects.user import User
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_user import (
    ApiSeedUser,
)


class ApiUser(ApiSeedUser["ApiUser", ApiRole, User, UserSaModel]):
    """API schema for user representation in recipes catalog context.

    Inherits from ApiSeedUser and overrides the domain type to use the
    recipes catalog specific User value object.

    Attributes:
        id: Required UUID identifier for the user.
        roles: Set of user roles with associated permissions.
    """

    id: UUIDIdRequired
    roles: Annotated[frozenset[ApiRole], Field(default_factory=frozenset)]

    def to_domain(self) -> User:
        """Convert API schema instance to domain model object.

        Returns:
            User domain object with roles and permissions.
        """
        return User(
            id=self.id,
            roles=frozenset(
                [
                    Role(name=role.name, permissions=frozenset(role.permissions))
                    for role in self.roles
                ]
            ),
        )

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Create API schema instance from domain model object.

        Args:
            domain_obj: User domain object to convert.

        Returns:
            ApiUser instance populated from domain object.
        """
        return cls(
            id=domain_obj.id,
            roles=frozenset([ApiRole.from_domain(role) for role in domain_obj.roles]),
        )

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Create API schema instance from ORM model.

        Args:
            orm_model: UserSaModel ORM instance to convert.

        Returns:
            ApiUser instance populated from ORM model.

        Notes:
            Handles legacy role data format with string-based permissions.
        """
        roles = []
        if orm_model.roles:
            for role_dict in orm_model.roles:
                if isinstance(role_dict, dict):
                    permissions = role_dict.get("permissions", [])
                    if isinstance(permissions, str):
                        permissions = [perm.strip() for perm in permissions.split(",")]
                    role = ApiRole(
                        name=role_dict.get("name", ""),
                        permissions=frozenset(permissions),
                    )
                    roles.append(role)
        return cls(id=orm_model.id, roles=frozenset(roles))
