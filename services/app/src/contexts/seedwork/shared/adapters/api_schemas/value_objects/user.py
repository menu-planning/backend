from typing import Any, Dict, TYPE_CHECKING
from pydantic import Field
from typing import Annotated

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel

if TYPE_CHECKING:
    from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole

class ApiSeedUser(BaseApiValueObject[SeedUser, UserSaModel]):
    """Schema for the SeedUser value object.
    
    Validation Strategy:
    - UUIDId: Built-in UUID format validation with length checks
    - BeforeValidator(validate_roles_collection): Complex type conversion with clear errors
    """
    
    id: UUIDIdRequired = Field(..., description="The unique identifier of the user")
    roles: Annotated[
        'frozenset[ApiSeedRole]',
        Field(default_factory=frozenset, description="Set of roles assigned to the user")
    ]

    @classmethod
    def from_domain(cls, domain_obj: SeedUser) -> "ApiSeedUser":
        """Convert a SeedUser domain object to an ApiSeedUser instance.
        
        Handles type conversions per docs/architecture/api-schema-patterns/patterns/type-conversions.md:
        - Domain set[SeedRole] → API frozenset[ApiSeedRole]
        
        Args:
            domain_obj: The SeedUser domain object to convert
            
        Returns:
            An ApiSeedUser instance
        """
        return cls(
            id=domain_obj.id,
            roles=frozenset(
                ApiSeedRole.from_domain(role) for role in domain_obj.roles
            ) if domain_obj.roles else frozenset()
        )

    def to_domain(self) -> SeedUser:
        """Convert the ApiSeedUser instance to a SeedUser domain object.
        
        Handles type conversions per documented patterns:
        - API frozenset[ApiSeedRole] → Domain set[SeedRole]
        
        Returns:
            A SeedUser instance
        """
        return SeedUser(
            id=self.id,
            roles=set(
                role.to_domain() for role in self.roles
            ) if self.roles else set()
        )

    @classmethod
    def from_orm_model(cls, orm_model: UserSaModel) -> "ApiSeedUser":
        """Convert an ORM model to an ApiSeedUser instance.
        
        Handles ORM → API conversions per documented patterns:
        - ORM list[RoleSaModel] → API frozenset[ApiSeedRole]
        
        Args:
            orm_model: The ORM model to convert
            
        Returns:
            An ApiSeedUser instance
        """
        return cls(
            id=orm_model.id,
            roles=frozenset(
                ApiSeedRole.from_orm_model(role) for role in orm_model.roles
            ) if orm_model.roles else frozenset()
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the ApiSeedUser instance to ORM model kwargs.
        
        Handles API → ORM conversions per documented patterns:
        - API frozenset[ApiSeedRole] → ORM kwargs with role data
        
        Note: In complex scenarios, role relationships may be handled 
        separately by repository layer for transaction management.
        
        Returns:
            Dictionary of kwargs for ORM model creation
        """
        return {
            "id": self.id,
            "roles": [role.to_orm_kwargs() for role in self.roles] if self.roles else []
        }
