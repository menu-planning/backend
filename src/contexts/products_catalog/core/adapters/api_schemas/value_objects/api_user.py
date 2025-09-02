from typing import Annotated, Any

from pydantic import Field
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.products_catalog.core.adapters.other_ctx_providers.iam.api_schemas.api_role import (
    ApiRole,
)
from src.contexts.products_catalog.core.domain.value_objects.role import Role
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_user import (
    ApiSeedUser,
)


class ApiUser(ApiSeedUser["ApiUser", ApiRole, User, UserSaModel]):
    """API schema for user value object in products catalog context.
    
    Attributes:
        id: User identifier.
        roles: Set of user roles.
    """

    id: UUIDIdRequired
    roles: Annotated[
        frozenset[ApiRole],
        Field(default_factory=frozenset)
    ]

    def to_domain(self) -> User:
        """Convert API schema to domain object.
        
        Returns:
            User domain object.
        """
        return User(
            id=self.id,
            roles=frozenset([Role(name=role.name, permissions=frozenset(role.permissions)) for role in self.roles])
        )

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Create API schema instance from domain object.
        
        Args:
            domain_obj: Domain user object.
            
        Returns:
            ApiUser instance.
        """
        return cls(
            id=domain_obj.id,
            roles=frozenset([ApiRole.from_domain(role) for role in domain_obj.roles])
        )

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiUser":
        """Create API schema instance from ORM model.
        
        Args:
            orm_model: SQLAlchemy user model.
            
        Returns:
            ApiUser instance.
        """
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
