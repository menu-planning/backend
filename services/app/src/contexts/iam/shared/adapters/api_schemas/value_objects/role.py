from pydantic import BaseModel
from src.contexts.iam.shared.domain.value_objects.role import Role


class ApiRole(BaseModel):
    name: str
    context: str
    permissions: list[str]

    @classmethod
    def from_domain(cls, domain_obj: Role) -> "ApiRole":
        try:
            return cls(
                name=domain_obj.name,
                context=domain_obj.context,
                permissions=domain_obj.permissions,
            )
        except Exception as e:
            raise ValueError(f"Failed to build from domain: {e}") from e

    def to_domain(self) -> Role:
        try:
            # if self.name == "administrator":
            #     return Role.administrator()
            # if self.name == "user_manager":
            #     return Role.user_manager()
            # if self.name == "role_manager":
            #     return Role.role_manager()
            # if self.name == "auditor":
            #     return Role.auditor()
            # if self.name == "user":
            #     return Role.user()
            # if self.name == "developer":
            #     return Role.developer()
            return Role(
                name=self.name,
                context=self.context,
                permissions=self.permissions,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
