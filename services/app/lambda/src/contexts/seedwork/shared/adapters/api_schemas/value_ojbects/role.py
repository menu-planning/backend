from pydantic import BaseModel
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole


class ApiSeedRole(BaseModel):
    name: str
    permissions: list[str]

    @classmethod
    def from_domain(cls, domain_obj: SeedRole) -> "ApiSeedRole":
        return cls(name=domain_obj.name, permissions=domain_obj.permissions)

    def to_domain(self, role_type: type[SeedRole]) -> SeedRole:
        return role_type(name=self.name, permissions=self.permissions)
