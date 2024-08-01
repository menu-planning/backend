from pydantic import UUID4, BaseModel
from src.contexts.iam.shared.adapters.api_schemas.value_objects.role import ApiRole
from src.contexts.iam.shared.domain.entities.user import User


class ApiUser(BaseModel):
    id: str
    roles: list[ApiRole]
    discarded: bool = False
    version: int = 1

    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        try:
            return cls(
                id=domain_obj.id,
                roles=(
                    [ApiRole.from_domain(i) for i in domain_obj.roles]
                    if domain_obj.roles
                    else []
                ),
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
        except Exception as e:
            raise ValueError(f"Failed to build from domain: {e}") from e
