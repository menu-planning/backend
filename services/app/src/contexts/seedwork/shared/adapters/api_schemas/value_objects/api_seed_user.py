from typing import Any, Dict, Generic, TypeVar
from pydantic import Field
from typing import Annotated

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.api_seed_role import ApiSeedRole
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel

D_USER = TypeVar("D_USER", bound=SeedUser)
S_USER = TypeVar("S_USER", bound=UserSaModel)
API_SEED_USER = TypeVar("API_SEED_USER", bound="ApiSeedUser")
API_SEED_ROLE = TypeVar("API_SEED_ROLE", bound=ApiSeedRole)

class ApiSeedUser(BaseApiValueObject[D_USER, S_USER], Generic[API_SEED_USER, API_SEED_ROLE, D_USER, S_USER]):
    """Schema for the SeedUser value object.
    
    Validation Strategy:
    - UUIDId: Built-in UUID format validation with length checks
    - BeforeValidator(validate_roles_collection): Complex type conversion with clear errors
    """
   
    id: UUIDIdRequired
    roles: Annotated[
        frozenset[API_SEED_ROLE],
        Field(default_factory=frozenset, description="Set of roles assigned to the user")
    ]

    @classmethod
    def from_domain(cls, domain_obj: D_USER) -> API_SEED_USER:
        """Convert a SeedUser domain object to an ApiSeedUser instance.
        
        Handles type conversions per docs/architecture/api-schema-patterns/patterns/type-conversions.md:
        - Domain set[SeedRole] → API frozenset[ApiSeedRole]
        
        Args:
            domain_obj: The SeedUser domain object to convert
            
        Returns:
            An ApiSeedUser instance
        """
        raise NotImplementedError("from_domain() method must be implemented by subclasses")

    def to_domain(self) -> D_USER:
        """Convert the ApiSeedUser instance to a SeedUser domain object.
        
        Handles type conversions per documented patterns:
        - API frozenset[ApiSeedRole] → Domain set[SeedRole]
        
        Returns:
            A SeedUser instance
        """
        raise NotImplementedError("to_domain() method must be implemented by subclasses")

    @classmethod
    def from_orm_model(cls, orm_model: S_USER) -> API_SEED_USER:
        """Convert an ORM model to an ApiSeedUser instance.
        
        Handles ORM → API conversions per documented patterns:
        - ORM list[RoleSaModel] → API frozenset[ApiSeedRole]
        
        Args:
            orm_model: The ORM model to convert
            
        Returns:
            An ApiSeedUser instance
        """
        raise NotImplementedError("from_orm_model() method must be implemented by subclasses")

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
