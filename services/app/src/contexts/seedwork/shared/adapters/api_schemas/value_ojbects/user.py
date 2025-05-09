from typing import ClassVar

from pydantic import BaseModel
from src.contexts.seedwork.shared.adapters.api_schemas.value_ojbects.role import (
    ApiSeedRole,
)
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser


class ApiSeedUser(BaseModel):
    id: str
    roles: list[ApiSeedRole]
    domain_user_type: ClassVar[type[SeedUser]] = SeedUser
    role_type: ClassVar[type[SeedRole]] = SeedRole

    @classmethod
    def from_domain(cls, domain_obj: SeedUser) -> "ApiSeedUser":
        """Creates an instance of `ApiUser` from a domain model object."""
        try:
            roles = (
                [ApiSeedRole.from_domain(role) for role in domain_obj.roles]
                if domain_obj.roles
                else []
            )
            return cls(id=domain_obj.id, roles=roles)
        except Exception as e:
            raise ValueError(f"Failed to build ApiSeedUser from domain instance: {e}")

    def to_domain(self) -> SeedUser:
        """Converts the instance to a domain model object."""
        try:
            roles = (
                [i.to_domain(self.role_type) for i in self.roles] if self.roles else []
            )
            return self.domain_user_type(id=self.id, roles=roles)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiSeedUser to domain model: {e}")
