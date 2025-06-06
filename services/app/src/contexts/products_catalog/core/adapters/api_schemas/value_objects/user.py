from typing import ClassVar, cast

from src.contexts.products_catalog.core.domain.value_objects.role import Role
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.user import (
    ApiSeedUser,
)
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser


class ApiUser(ApiSeedUser):
    domain_user_type: ClassVar[type[SeedUser]] = User
    role_type: ClassVar[type[SeedRole]] = Role
    
    def to_domain(self) -> User:
        return cast(User, super().to_domain())
    
    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        base = super().from_domain(domain_obj)
        return cast(ApiUser, base)
